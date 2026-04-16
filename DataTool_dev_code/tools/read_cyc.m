function T = read_cyc(cyc_path)
%READ_CYC  PNE .cyc 바이너리 → [Time, Voltage, Current, Temp] table
%   T = read_cyc('C:\...\test.cyc')

fid = fopen(cyc_path, 'r', 'l');

% 헤더
fseek(fid, hex2dec('148'), 'bof');
n_fields = fread(fid, 1, 'uint32');
fseek(fid, hex2dec('14C'), 'bof');
field_ids = fread(fid, n_fields, 'uint16');

% 데이터
data_start = hex2dec('1B0');
fseek(fid, 0, 'eof');
n_rec = floor((ftell(fid) - data_start) / (n_fields * 4));
fseek(fid, data_start, 'bof');
raw = fread(fid, [n_fields, n_rec], 'single')';
fclose(fid);

% FID 위치 찾기: 7=TotalTime(s), 1=Voltage(mV), 2=Current(mA), 12=Temp(C)
targets = [7, 1, 2, 12];
names   = {'Time_s', 'Voltage_mV', 'Current_mA', 'Temp_C'};
cols = zeros(1, 4);
for k = 1:4
    idx = find(field_ids == targets(k), 1);
    if isempty(idx), error('FID %d not found', targets(k)); end
    cols(k) = idx;
end

T = array2table(raw(:, cols), 'VariableNames', names);
end
