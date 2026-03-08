#!/bin/bash
sudo mount -t ext4 /dev/sdf1 /media/backup
sudo rsync -av /media/megadrive/files /media/backup/files
# sudo rsync -av /etc/awstats /media/backup/awstats/config
# sudo rsync -av /var/lib/awstats /media/backup/awstats/data
sudo rsync -av /home/timmy /media/backup/timmy
sudo rsync -av /etc/apache2 /media/backup/apache
sudo rsync -av /var/lib/mysql /media/backup/mysql/data

sudo mysqldump -uroot -p<password> mastersystem | bzip2 -c > /media/backup/mysql/$(date +%Y-%m-%d-%H.%M.%S).sql.bz2

