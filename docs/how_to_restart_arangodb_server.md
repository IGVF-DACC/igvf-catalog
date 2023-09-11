# How to Restart ArangoDB Server on AWS EC2 instance

Sometime the database server is down due to various reasons. You can go to [database interface](https://db.catalog.igvf.org/_db/igvf/_admin/aardvark/index.html#nodes) to check if any server node is down.

This is what you need to do in order to restart the server node:

1. Check which server node is down. Find the coresponding EC2 instance by checking the node endpoint, then restart that EC2 instance. Sometime the EC2 instance can be not responding, in that case stop and start the instance.

2. Log into the restarted EC2 instance. Check the disk space first to make sure there is still a lot of free space for loading data. If not, you may need to increase the disk volumn first before you restart the arangoDB server.

3. Go to the home directry and excute this command below. The IP in the end must be of a node that's up and running so the new process knows where to connect

``` bash
arangodb --auth.jwt-secret=/etc/arangodb.secret --starter.data-dir=./data2 --starter.join {running_server_IP}:{port}&
```
