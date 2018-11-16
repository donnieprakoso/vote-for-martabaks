#!/bin/sh
read -p 'Hello. Please provide S3 bucket name with website configuration: ' s3bucket
while true; do
    read -p "Sync current directory with S3 bucket. Shall I begin? " yn
    case $yn in
        [Yy]* ) aws s3 sync --delete --acl "public-read" . s3://$s3bucket --delete; break;;
        [Nn]* ) exit;;
        * ) echo "Please answer yes or no.";;
    esac
done
