SYSTEMD_PATH=/lib/systemd/system
ROOT_FOLDER=$(dirname $(readlink -e $PWD))

echo "[Unit]
Description= <Polar Scanner>
ConditionPathExists=$ROOT_FOLDER/client-server-mode
After=multi-user.target

[Service]
Type=idle
WorkingDirectory=$ROOT_FOLDER/client-server-mode
ExecStart=/usr/bin/python3.5 $ROOT_FOLDER/client-server-mode/polar_scanner_net.py
Restart=always

[Install]
WantedBy=multi-user.target" > $SYSTEMD_PATH/polar_scan.service

systemctl daemon-reload
systemctl start polar_scan.service

