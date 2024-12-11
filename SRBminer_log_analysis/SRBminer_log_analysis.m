% SRBminer log analysis
Time = [];
TimeValid = [];
TimeValidDiff = [];
TimeReject = [];
TimeRejectDiff = [];
TimeRestart = [];
TimeRestartDiff = [];

path = "miner14.log";
fid = fopen(path);

while ~feof(fid)
    line_ex = fgetl(fid);  % read line excluding newline character
    if contains(line_ex, 'result accepted') || contains(line_ex, 'result rejected') || contains(line_ex, 'Restarting miner')
        Time = [Time; datetime(line_ex(2 : 20))]; % event time stamp
        if length(Time) > 1
            if contains(line_ex, 'result accepted') % specific event
                TimeValid = [TimeValid Time(end)];
                TimeValidDiff = [TimeValidDiff seconds(Time(end) - Time(end - 1))];
            end
            if contains(line_ex, 'result rejected')
                TimeReject = [TimeReject Time(end)];
                TimeRejectDiff = [TimeRejectDiff seconds(Time(end) - Time(end - 1))];
            end
            if contains(line_ex, 'Restarting miner')
                TimeRestart = [TimeRestart Time(end)];
                TimeRestartDiff = [TimeRestartDiff seconds(Time(end) - Time(end - 1))];
            end
        end
    end
end

fclose(fid);
%%
figure;
hold on;
plot(TimeValid, TimeValidDiff, "Marker", ".");
scatter(TimeReject, TimeRejectDiff, 100, [0.8500 0.3250 0.0980], ".");
scatter(TimeRestart, TimeRestartDiff, [], [0.9290 0.6940 0.1250], "*");
ylabel("Share find time(s)")
title('#11 rig');
legend("share accepted", "share rejected", "miner restart");
hold off;

figure;
pd1 = createFit(TimeValidDiff);

function pd1 = createFit(TimeDiff)
%CREATEFIT    Create plot of datasets and fits
%   PD1 = CREATEFIT(TIMEDIFF)
%   Creates a plot, similar to the plot in the main distribution fitter
%   window, using the data that you provide as input.  You can
%   apply this function to the same data you used with distributionFitter
%   or with different data.  You may want to edit the function to
%   customize the code and this help message.
%
%   Number of datasets:  1
%   Number of fits:  1
%
%   See also FITDIST.

% This function was automatically generated on 07-Nov-2023 22:56:49

% Output fitted probablility distribution: PD1

% Data from dataset "TimeDiff data":
%    Y = TimeDiff

% Force all inputs to be column vectors
TimeDiff = TimeDiff(:);

% Prepare figure
clf;
hold on;
LegHandles = []; LegText = {};


% --- Plot data originally in dataset "TimeDiff data"
[CdfF,CdfX] = ecdf(TimeDiff,'Function','cdf');  % compute empirical cdf
BinInfo.rule = 1;
[~,BinEdge] = internal.stats.histbins(TimeDiff,[],[],BinInfo,CdfF,CdfX);
[BinHeight,BinCenter] = ecdfhist(CdfF,CdfX,'edges',BinEdge);
hLine = bar(BinCenter,BinHeight,'hist');
set(hLine,'FaceColor','none','EdgeColor',[0.333333 0 0.666667],...
    'LineStyle','-', 'LineWidth',1);
xlabel('Data');
ylabel('Density')
LegHandles(end+1) = hLine;
LegText{end+1} = 'TimeDiff data';

% Create grid where function will be computed
XLim = get(gca,'XLim');
XLim = XLim + [-1 1] * 0.01 * diff(XLim);
XGrid = linspace(XLim(1),XLim(2),100);


% --- Create fit "fit 1"

% Fit this distribution to get parameter values
% To use parameter estimates from the original fit:
%     pd1 = ProbDistUnivParam('exponential',[ 18.33689126084])
pd1 = fitdist(TimeDiff, 'exponential');
YPlot = pdf(pd1,XGrid);
hLine = plot(XGrid,YPlot,'Color',[1 0 0],...
    'LineStyle','-', 'LineWidth',2,...
    'Marker','none', 'MarkerSize',6);
LegHandles(end+1) = hLine;
LegText{end+1} = 'fit 1';

% Adjust figure
box on;
hold off;

% Create legend from accumulated handles and labels
hLegend = legend(LegHandles,LegText,'Orientation', 'vertical', 'FontSize', 9, 'Location', 'northeast');
set(hLegend,'Interpreter','none');
end