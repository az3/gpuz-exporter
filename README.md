# gpuz-exporter

This Python 3 script converts GPU-Z text output into Prometheus metric format and serves on port 9184.

Sample output;
```
$ curl -s http://localhost:9184/metrics | head -6
...
# HELP gpuz_gpu_clock GPU Clock [MHz]
# TYPE gpuz_gpu_clock gauge
gpuz_gpu_clock{localizedSrcName="GPU Clock",srcUnits="MHz"} 1785.0
```

GPU-Z provides monitoring data in text format.

Newest version can be found here: https://www.techpowerup.com/download/techpowerup-gpu-z/

Sample text output;
```
$ head -2 gpuz.txt
        Date        , GPU Clock [MHz] , Memory Clock [MHz] , GPU Temperature [°C] , Hot Spot [°C] , Memory Temperature [°C] , Fan 1 Speed (%) [%] , Fan 1 Speed (RPM) [RPM] , Fan 2 Speed (%) [%] , Fan 2 Speed (RPM) [RPM] , Memory Used [MB] , GPU Load [%] , Memory Controller Load [%] , Video Engine Load [%] , Bus Interface Load [%] , Board Power Draw [W] , GPU Chip Power Draw [W] , MVDDC Power Draw [W] , PWR_SRC Power Draw [W] , PWR_SRC Voltage [V] , PCIe Slot Power [W] , PCIe Slot Voltage [V] , 8-Pin #1 Power [W] , 8-Pin #1 Voltage [V] , 8-Pin #2 Power [W] , 8-Pin #2 Voltage [V] , Power Consumption (%) [% TDP] , PerfCap Reason [] , GPU Voltage [V] , CPU Temperature [°C] , System Memory Used [MB] ,
2024-01-14 18:41:07 ,        1785.0   ,           1187.7   ,               48.7   ,        64.1   ,                  58.0   ,                 0   ,                     0   ,                 0   ,                     0   ,           3543   ,          7   ,                        1   ,                   0   ,                    0   ,              114.3   ,                  28.2   ,               59.5   ,                 69.2   ,              12.2   ,              24.5   ,                12.2   ,             41.1   ,               12.2   ,             48.7   ,               12.2   ,                        33.6   ,              16   ,        0.9180   ,               67.5   ,                 17888   ,
...
```

The header in file is converted into Prometheus labels.

gpuz_exporter.py tails the GPU Z file "GPU-Z Sensor Log.txt" in a separate thread. Everytime GET /metrics is requested, http server publishes the last read values.
