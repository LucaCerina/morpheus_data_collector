SYSTEMD_PATH=/lib/systemd/system


echo "[UNIT]
Descriptions= <Polar Scanner>
ConditionPathExists=$PWD/../client-server-mode
After=multi-user.target

[Service]
Type=idle
User=pi
Group=users
ExecStart=sudo /usr/bin/python3.5 $PWD/../client-server-mode/polar_scanner_net.py
Restart=always

[Install]
WantedBy=multi-user.target" > $SYSTEMD_PATH/polar_scan.service

systemctl start polar_scan.service

