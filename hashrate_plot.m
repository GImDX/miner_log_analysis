%内核选择lolminer/nbminer
global options t hashrate hashrate_Record ax_hashrate xlimit Title_Cache Mode
Mode = 'lolminer';

% 删除现有的定时器，重新创建一个定时器
try
    stop(timerfindall);
    delete(timerfindall);
catch
end

Title_Cache = [];
timer_readhashrate = timer;
timer_readhashrate.StartDelay = 0;
timer_readhashrate.Period = 2;
% 周期性执行,fixedSpacing模式
timer_readhashrate.ExecutionMode = 'fixedSpacing';
timer_readhashrate.TimerFcn = @timer_handler;

xlimit = 600;
options = weboptions('ContentType', 'json', 'CharacterEncoding', 'utf-8', 'ArrayFormat', 'csv');
S = struct();

%while isempty(fieldnames(S))

switch Mode
    case 'nbminer'
        try
            S = webread('http://127.0.0.1:22333/api/v1/status', options);
            t = datetime('now', 'TimeZone', 'local', 'Format', 'd-MMM-y HH:mm:ss Z');
            t0 = seconds(S.start_time) + datetime(1970, 01, 01, 00, 00, 00);
            hashrate = S.miner.total_hashrate_raw / 1e6;
        catch
            warning('Attempt to Read RESTful WEB failed.Please check.');
            t = datetime('now', 'TimeZone', 'local', 'Format', 'd-MMM-y HH:mm:ss Z');
            t0 = t;
            hashrate = 0;
            pause(2);
            clc;
        end
        hashrate_Record = hashrate;
    case 'lolminer'
        try
            S = webread('http://127.0.0.1:8020', options);
            t = datetime('now', 'TimeZone', 'local', 'Format', 'd-MMM-y HH:mm:ss Z');
            t0 = seconds(S.Session.Startup) + datetime(1970, 01, 01, 00, 00, 00);
            hashrate = S.Algorithms.Total_Performance;
        catch
            warning('Attempt to Read RESTful WEB failed.Please check.');
            t = datetime('now', 'TimeZone', 'local', 'Format', 'd-MMM-y HH:mm:ss Z');
            t0 = t;
            hashrate = 0;
            pause(2);
            clc;
        end
        hashrate_Record = hashrate;
    otherwise
        error('Sofeware name error.');
end




%plot
figure(114514);
clf(figure(114514));
ax_hashrate = axes(figure(114514));

%启动定时器
start(timer_readhashrate);

function timer_handler(~, ~)
read_web_success = 0;
global options t hashrate hashrate_Record ax_hashrate xlimit Title_Cache Mode

while ~read_web_success

    switch Mode
        case 'nbminer'
            try
                S = webread('http://127.0.0.1:22333/api/v1/status', options);
                read_web_success = 1;
                t = [t datetime('now', 'TimeZone', 'local', 'Format', 'd-MMM-y HH:mm:ss Z')];
                hashrate = [hashrate S.miner.total_hashrate_raw / 1e6];

                if length(t) > xlimit
                    t = t(2:xlimit + 1);
                    hashrate = hashrate(2:xlimit + 1);
                end

                plot(ax_hashrate, t, hashrate, 'blue');
                ax_hashrate.Title.String = {S.miner.devices.info;S.stratum.algorithm};
                Title_Cache = S.miner.devices.info;
                ax_hashrate.XLabel.String = 'Time/utc+8';
                ax_hashrate.YLabel.String = 'Hashrate/MH/s';
                ax_hashrate.XMinorGrid = 'on';
                ax_hashrate.YMinorGrid = 'on';
                ax_hashrate.XLim = [t(1), t(end)];
            catch
                warning('Attempt to Read RESTful WEB failed.Please check.');
                %S = webread('http://127.0.0.1:22333/api/v1/status', options);
                read_web_success = 1;
                t = [t datetime('now', 'TimeZone', 'local', 'Format', 'd-MMM-y HH:mm:ss Z')];
                hashrate = [hashrate 0];

                if length(t) > xlimit
                    t = t(2:xlimit + 1);
                    hashrate = hashrate(2:xlimit + 1);
                end

                plot(ax_hashrate, t, hashrate, 'blue');
                ax_hashrate.Title.String = Title_Cache;
                ax_hashrate.XLabel.String = 'Time/utc+8';
                ax_hashrate.YLabel.String = 'Hashrate/MH/s';
                ax_hashrate.XMinorGrid = 'on';
                ax_hashrate.YMinorGrid = 'on';
                ax_hashrate.XLim = [t(1), t(end)];
                pause(2);
                clc;
            end
            hashrate_Record = [hashrate_Record hashrate(end)];
        case 'lolminer'
            try
                S = webread('http://127.0.0.1:8020', options);
                read_web_success = 1;
                t = [t datetime('now', 'TimeZone', 'local', 'Format', 'd-MMM-y HH:mm:ss Z')];
                hashrate = [hashrate S.Algorithms.Total_Performance];

                if length(t) > xlimit
                    t = t(2:xlimit + 1);
                    hashrate = hashrate(2:xlimit + 1);
                end

                plot(ax_hashrate, t, hashrate, 'blue');
                ax_hashrate.Title.String = {S.Workers.Name;S.Algorithms.Algorithm;S.Algorithms.Pool;S.Algorithms.User};
                Title_Cache = S.Workers.Name;
                ax_hashrate.XLabel.String = 'Time/utc+8';
                ax_hashrate.YLabel.String = 'Hashrate/MH/s';
                ax_hashrate.XMinorGrid = 'on';
                ax_hashrate.YMinorGrid = 'on';
                ax_hashrate.XLim = [t(1), t(end)];
            catch
                warning('Attempt to Read RESTful WEB failed.Please check.');
                %S = webread('http://127.0.0.1:22333/api/v1/status', options);
                read_web_success = 1;
                t = [t datetime('now', 'TimeZone', 'local', 'Format', 'd-MMM-y HH:mm:ss Z')];
                hashrate = [hashrate 0];

                if length(t) > xlimit
                    t = t(2:xlimit + 1);
                    hashrate = hashrate(2:xlimit + 1);
                end

                plot(ax_hashrate, t, hashrate, 'blue');
                ax_hashrate.Title.String = Title_Cache;
                ax_hashrate.XLabel.String = 'Time/utc+8';
                ax_hashrate.YLabel.String = 'Hashrate/MH/s';
                ax_hashrate.XMinorGrid = 'on';
                ax_hashrate.YMinorGrid = 'on';
                ax_hashrate.XLim = [t(1), t(end)];
                pause(2);
                clc;
            end
            hashrate_Record = [hashrate_Record hashrate(end)];
        otherwise
            error('Sofeware name error.');
    end


end

end
