import json
import hashlib
from hashlib import blake2b
from typing import List

q = int("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141", 16)

class AutolykosPowScheme:
    def __init__(self, k: int, n: int):
        self.k = k
        self.n = n
        self.InitialVersion = 1
        self.NBase = 2 ** n
        self.IncreaseStart = 600 * 1024
        self.IncreasePeriodForN = 50 * 1024
        self.NMaxHeight = 4198400
        self.M = b''.join(i.to_bytes(8, 'big') for i in range(1024))

    def calcN(self, version: int, height: int) -> int:
        if version == self.InitialVersion:
            return self.NBase
        height = min(height, self.NMaxHeight)
        if height < self.IncreaseStart:
            return self.NBase
        iters = (height - self.IncreaseStart) // self.IncreasePeriodForN + 1
        step = self.NBase
        for _ in range(iters):
            step = (step // 100) * 105
        return step

    def getB(self, nbits: int) -> int:
        target = decode_compact_bits(nbits)
        return q // target

    def msgByHeader(self, header: dict) -> bytes:
        return blake2b256(bytes_without_pow(header))

    def genIndexes(self, seed: bytes, N: int) -> List[int]:
        hash_ = blake2b256(seed)
        # print("Scala hash =", hash_.hex())

        extended_hash = hash_ + hash_[:3]  # 32 + 3 = 35 bytes
        # print("Scala extendedHash =", extended_hash.hex())
        # print("k =", self.k)

        indexes = []
        for i in range(self.k):
            slice_ = extended_hash[i:i+4]
            idx = int.from_bytes(slice_, 'big') % N
            # print(f"i = {i}, slice = {slice_.hex()}, idx = {idx}")
            indexes.append(idx)
        return indexes
    
    def genElement(self, version: int, msg: bytes, pk, w, index_bytes: bytes, height_bytes: bytes) -> int:
        if version == 1:
            # Autolykos v1: H(j | M | pk | m | w) mod q
            assert msg is not None and pk is not None and w is not None
            input_bytes = index_bytes + self.M + pk + msg + w
            return hash_mod_q(input_bytes)
        else:
            # Autolykos v2: hash(index_bytes ++ height_bytes ++ M).drop(1)
            input_bytes = index_bytes + height_bytes + self.M
            full_hash = blake2b(input_bytes, digest_size=32).digest()
            element = int.from_bytes(full_hash[1:], 'big')  # drop first byte
            return element

    def hitForVersion2ForMessage(self, msg: bytes, nonce: bytes, h: bytes, N: int) -> int:
        # Step 1: Blake2b256(msg || nonce)
        hash_input = msg + nonce
        hash_result = blake2b256(hash_input)
        # print(f"[Step 1] hash(msg || nonce) = {hash_result.hex()}")

        # Step 2: 取 hash 的最后 8 字节，并转换为无符号整数
        last8 = hash_result[-8:]
        prei8 = int.from_bytes(last8, 'big')
        # print(f"[Step 2] last 8 bytes = {last8.hex()}")
        # print(f"[Step 2] prei8 = {prei8}")

        # Step 3: i = prei8 mod N，然后转换成 4 字节
        i_mod = prei8 % N
        i_bytes = int_to_bytes(i_mod, 4)
        # print(f"[Step 3] i_mod (prei8 % N) = {i_mod}")
        # print(f"[Step 3] i_bytes = {i_bytes.hex()}")

        # Step 4: Blake2b256(i || h || M).drop(1)
        f_input = i_bytes + h + self.M
        f_full = blake2b(f_input, digest_size=32).digest()
        f = f_full[1:]
        # print(f"[Step 4] h = {h.hex()}")
        # print(f"[Step 4] M = {self.M.hex()}")
        # print(f"[Step 4] f_full = {f_full.hex()}")
        # print(f"[Step 4] f = f_full[1:] = {f.hex()}")

        # Step 5: seed = f || msg || nonce
        seed = f + msg + nonce
        # print(f"[Step 5] seed = f || msg || nonce = {seed.hex()}")

        # Step 6: genIndexes(seed, N)
        indexes = self.genIndexes(seed, N)
        # print(f"[Step 6] indexes = {indexes}")

        # Step 7: elems = genElement(...) for each index
        elems = []
        for idx in indexes:
            idx_bytes = int_to_bytes(idx, 4)
            elem = self.genElement(2, msg, None, None, idx_bytes, h)
            elems.append(elem)
            # print(f"[Step 7] idxBytes = {idx_bytes.hex()}")
            # print(f"[Step 7] element for index {idx} = {elem}")

        # Step 8: f2 = sum(elems)
        f2 = sum(elems)
        # print(f"[Step 8] f2 = sum(elems) = {f2}")

        # Step 9: f2_bytes: 取最后32字节，并补齐到32字节（右对齐）
        f2_bytes = f2.to_bytes((f2.bit_length() + 7) // 8, 'big')[-32:].rjust(32, b'\x00')
        # print(f"[Step 9] f2_bytes (right 32 bytes, padded) = {f2_bytes.hex()}")

        # Step 10: hit = blake2b256(f2_bytes) → to_bigint
        ha = blake2b256(f2_bytes)
        hit = to_bigint(ha)
        # print(f"[Step 10] hash(f2_bytes) = {ha.hex()}")
        # print(f"[Step 10] hit = {hit}")

        return hit


    def hitForVersion2(self, header: dict) -> int:
        msg = self.msgByHeader(header)
        nonce = bytes.fromhex(header["powSolutions"]["n"])
        h = int_to_bytes(header["height"], 4)
        N = self.calcN(header["version"], header["height"])

        # print(f"hitForVersion2->计算得到的 msg = {msg.hex()}")
        # print(f"hitForVersion2->计算得到的 nonce = {nonce.hex()}")
        # print(f"hitForVersion2->计算得到的 height = {h.hex()}")
        # print(f"hitForVersion2->计算得到的 calcN = {N}")
        return self.hitForVersion2ForMessage(msg, nonce, h, N)
    

    def checkPowForVersion2(self, header: dict) -> bool:
        b = self.getB(header["nBits"])
        hit = self.hitForVersion2(header)
        return hit < b
    
    def powHit(self, header: dict) -> int:
        if header["version"] == self.InitialVersion:
            return int(header["powSolutions"]["d"])
        else:
            return self.hitForVersion2(header)
    
    def realDifficulty(self, header: dict) -> int:
        hit = self.powHit(header)
        return q // hit

# --- Utility functions ---
def hash_mod_q(data: bytes) -> int:
    digest = blake2b(data, digest_size=32).digest()
    return int.from_bytes(digest, 'big') % q

def blake2b256(data: bytes) -> bytes:
    return hashlib.blake2b(data, digest_size=32).digest()

def to_bigint(b: bytes) -> int:
    return int.from_bytes(b, byteorder='big')

def to_bytes_bigint(value: int, length: int) -> bytes:
    return value.to_bytes(length, byteorder='big')

def int_to_bytes(n: int, length: int) -> bytes:
    return n.to_bytes(length, 'big')

def decode_compact_bits(compact: int) -> int:
    size = (compact >> 24) & 0xFF
    bytes_ = [0] * (4 + size)
    bytes_[3] = size
    if size >= 1:
        bytes_[4] = (compact >> 16) & 0xFF
    if size >= 2:
        bytes_[5] = (compact >> 8) & 0xFF
    if size >= 3:
        bytes_[6] = compact & 0xFF
    return decode_mpi(bytes_)

def decode_mpi(mpi_bytes: List[int]) -> int:
    length = int.from_bytes(bytearray(mpi_bytes[0:4]), 'big')
    if length == 0:
        return 0
    buf = bytearray(mpi_bytes[4:4+length])
    is_negative = (buf[0] & 0x80) == 0x80
    if is_negative:
        buf[0] = buf[0] & 0x7F
    result = int.from_bytes(buf, 'big')
    return -result if is_negative else result

def vlq_encode_uint(value: int) -> bytes:
    result = bytearray()
    while True:
        to_write = value & 0x7F
        value >>= 7
        if value:
            result.append(to_write | 0x80)
        else:
            result.append(to_write)
            break
    return bytes(result)

def bytes_without_pow(header: dict) -> bytes:
    fields = [
        header["version"].to_bytes(1, 'big'),
        bytes.fromhex(header["parentId"]),
        bytes.fromhex(header["adProofsRoot"]),
        bytes.fromhex(header["transactionsRoot"]),
        bytes.fromhex(header["stateRoot"]),
        vlq_encode_uint(header["timestamp"]),
        bytes.fromhex(header["extensionHash"]),
        header["nBits"].to_bytes(4, 'big'),
        vlq_encode_uint(header["height"]),
        parse_votes(header["votes"]),
    ]
    if header["version"] > 1:
        unparsed = bytes.fromhex(header.get("unparsedBytes", ""))
        fields.append(len(unparsed).to_bytes(1, 'big'))
        fields.append(unparsed)
    return b''.join(fields)

def parse_votes(v):
    if isinstance(v, list):
        # votes: [0, 0, 0] → bytes([0, 0, 0])
        return bytes(v)
    elif isinstance(v, str):
        # votes: "000000" (hex string) → bytes.fromhex("000000")
        return bytes.fromhex(v)
    else:
        raise ValueError(f"Unsupported votes format: {v}")


# # --- JSON 输入 ---
# header_json_str =       """
#         {
#           "extensionId" : "00cce45975d87414e8bdd8146bc88815be59cd9fe37a125b5021101e05675a18",
#           "difficulty" : "16384",
#           "votes" : "000000",
#           "timestamp" : 4928911477310178288,
#           "size" : 223,
#           "stateRoot" : "5c8c00b8403d3701557181c8df800001b6d5009e2201c6ff807d71808c00019780",
#           "height" : 614400,
#           "nBits" : 37748736,
#           "version" : 2,
#           "id" : "5603a937ec1988220fc44fb5022fb82d5565b961f005ebb55d85bd5a9e6f801f",
#           "adProofsRoot" : "5d3f80dcff7f5e7f59007294c180808d0158d1ff6ba10000f901c7f0ef87dcff",
#           "transactionsRoot" : "f17fffacb6ff7f7f1180d2ff7f1e24ffffe1ff937f807f0797b9ff6ebdae007e",
#           "extensionHash" : "1480887f80007f4b01cf7f013ff1ffff564a0000b9a54f00770e807f41ff88c0",
#           "powSolutions" : {
#             "pk" : "03bedaee069ff4829500b3c07c4d5fe6b3ea3d3bf76c5c28c1d4dcdb1bed0ade0c",
#             "n" : "0000000000003105"
#            },
#           "adProofsId" : "dec129290a763f4de41f04e87e2b661dd59758af6bdd00dd51f5d97c3a8cb9b5",
#           "transactionsId" : "eba1dd82cf51147232e09c1f72b37c554c30f63274d5093bff36849a83472a42",
#           "parentId" : "ac2101807f0000ca01ff0119db227f202201007f62000177a080005d440896d0"
#         }
#       """
# header = json.loads(header_json_str)
# pow = AutolykosPowScheme(k=32, n=26)

# # --- 验证blake2b256和base16.encode等效 ---
# # 来自 LiteClientExamples.scala 示例中的 msgPreimageBase16
# msg_preimage_hex = "01fb9e35f8a73c128b73e8fde5c108228060d68f11a69359ee0fb9bfd84e7ecde6d19957ccbbe75b075b3baf1cac6126b6e80b5770258f4cec29fbde92337faeec74c851610658a40f5ae74aa3a4babd5751bd827a6ccc1fe069468ef487cb90a8c452f6f90ab0b6c818f19b5d17befd85de199d533893a359eb25e7804c8b5d7514d784c8e0e52dabae6e89a9d6ed9c84388b228e7cdee09462488c636a87931d656eb8b40f82a507008ccacbee05000000"
# # 正确结果
# expected_msg_test = "6cb37d0a202bc2984f43de003cbc5558804db45798d0fc8faae7390b96d42d15"
# # 解码并计算
# msg_preimage_bytes = bytes.fromhex(msg_preimage_hex)
# calculated_msg_test = blake2b256(msg_preimage_bytes).hex()
# # 输出验证
# print("计算得到的 msg:", calculated_msg_test)
# print("预期的目标 msg:", expected_msg_test)
# print("是否匹配:", "✅\n" if calculated_msg_test == expected_msg_test else "❌ 不匹配\n")


# # --- 打印解析字段 ---
# version = header["version"].to_bytes(1, 'big')
# height = int(header['height'])
# nbits = header["nBits"].to_bytes(4, 'big')
# nonce = bytes.fromhex(header['powSolutions']['n'])
# print(f"height = {height}")
# print(f"nBits = 0x{nbits.hex()}")
# print(f"powSolution.n = 0x{nonce.hex()}")


# # --- 计算 N 值 ---
# n_val = pow.calcN(version, height)
# expected_n_val = 70464240
# print(f"预期的目标 calcN = {expected_n_val}")
# print(f"计算得到的 calcN = {n_val}")
# print("是否匹配:", "✅\n" if n_val == expected_n_val else "❌ 不匹配\n")


# # --- 构造 msg 并打印 hex ---
# msg_bytes = bytes_without_pow(header)
# msg = blake2b256(msg_bytes)
# msg_hex = msg.hex()
# expected_msg = "548c3e602a8f36f8f2738f5f643b02425038044d98543a51cabaa9785e7e864f"
# # print("Full serialized bytesWithoutPow (hex):")
# # print(msg_bytes.hex())  # 完整打印拼接后的原始字节
# print(f"预期的目标 msg = {expected_msg}")
# print(f"计算得到的 msg = {msg_hex}")
# print("是否匹配:", "✅\n" if msg_hex == expected_msg else "❌ 不匹配\n")


# # --- 计算 difficulty 值 ---
# nbits = header['nBits']  # 0x02400000
# difficultty = decode_compact_bits(nbits)
# expected_difficulty = int(header['difficulty'])
# print(f"预期的目标 difficulty = {expected_difficulty}")
# print(f"计算得到的 difficulty = {difficultty}")
# print("是否匹配:", "✅\n" if difficultty == expected_difficulty else "❌ 不匹配\n")


# # --- 计算 getB 值 ---
# b = pow.getB(nbits)
# expected_b = int("7067388259113537318333190002971674063283542741642755394446115914399301849")
# print(f"预期的目标 getB = {expected_b}")
# print(f"计算得到的 getB = {b}")
# print("是否匹配:", "✅\n" if b == expected_b else "❌ 不匹配\n")


# # --- 计算 hitForVersion2 值 ---
# expected_ha = "0002fcb113fe65e5754959872dfdbffea0489bf830beb4961ddc0e9e66a1412a"
# expected_hit = to_bigint(bytes.fromhex("0002fcb113fe65e5754959872dfdbffea0489bf830beb4961ddc0e9e66a1412a"))
# hit = pow.hitForVersion2(header)
# ha = to_bytes_bigint(hit, 32)
# print(f"预期的目标 hit = {expected_hit}")
# print(f"计算得到的 hit = {hit}")
# print(f"预期的目标 ha = {expected_ha}")
# print(f"计算得到的 ha = {ha.hex()}")
# print("是否匹配:", "✅\n" if hit == expected_hit else "❌ 不匹配\n")


# real_diff = pow.realDifficulty(header)
# print(f"✅ Real difficulty = {real_diff}")

# print("solution验证是否通过:", "✅\n" if pow.checkPowForVersion2(header) else "❌ 无效solution\n")


with open("header.json", "r", encoding="utf-8") as f:
    full_json = json.load(f)
    header = full_json["block"]["header"]

pow = AutolykosPowScheme(k=32, n=26)

# --- 打印解析字段 ---
version = header["version"].to_bytes(1, 'big')
height = int(header['height'])
nonce = bytes.fromhex(header['powSolutions']['n'])
block_id = header['id']

# --- 计算 N 值 ---
n_val = pow.calcN(version, height)

# --- 构造 msg 并打印 hex ---
msg_bytes = bytes_without_pow(header)
msg = blake2b256(msg_bytes)
msg_hex = msg.hex()

# --- 计算 difficulty 值 ---
nbits = header['nBits']  # 0x02400000
difficultty = decode_compact_bits(nbits)
expected_difficulty = int(header['difficulty'])

# --- 计算 getB 值 ---
b = pow.getB(nbits)

# --- 计算 hitForVersion2 值 ---
hit = pow.hitForVersion2(header)
ha = to_bytes_bigint(hit, 32)

# --- 计算 real_diff ---
real_diff = pow.realDifficulty(header)

# --- print ---
nbits = header["nBits"].to_bytes(4, 'big')
print("ERGO")
print(f"version                  = {version.hex()}")
print(f"height                   = {height}")
print(f"block id                 = 0x{block_id}")
print(f"nBits                    = 0x{nbits.hex()}")
print(f"powSolution.n            = 0x{nonce.hex()}")
print(f"calculated calcN         = 0x{n_val}")
print(f"calculated msg           = 0x{msg_hex}")
print(f"calculated getB          = 0x{b}")
print(f"calculated hit           = 0x{hit}")
print(f"calculated ha            = 0x{ha.hex()}")

print(f"difficulty               = {expected_difficulty}")
print(f"decodeCompactBits        = {difficultty}  {difficultty / 1e12} T")
print(f"real difficulty          = {real_diff}  {real_diff / 1e12} T")
print("nBits match difficulty ?:", "✅" if difficultty == expected_difficulty else "❌")
print("solution validated     ?:", "✅" if pow.checkPowForVersion2(header) else "❌")
