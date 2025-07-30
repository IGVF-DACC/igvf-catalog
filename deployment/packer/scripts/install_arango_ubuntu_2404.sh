set -ex
sudo apt-get update
sudo apt-get install -y wget debconf-utils unzip
echo 'deb https://download.arangodb.com/arangodb312/DEBIAN/ /' | sudo tee /etc/apt/sources.list.d/arangodb.list
wget -qO- https://download.arangodb.com/arangodb312/DEBIAN/Release.key | sudo tee /etc/apt/trusted.gpg.d/Release.asc
sudo apt-get update

echo arangodb3       arangodb3/backup        boolean false | sudo debconf-set-selections
echo arangodb3       arangodb3/upgrade       boolean false | sudo debconf-set-selections
echo arangodb3       arangodb3/password password "" | sudo debconf-set-selections
echo arangodb3       arangodb3/password_again password "" | sudo debconf-set-selections

sudo apt-get install -y arangodb3
# make sure this service won't interfere with the arango cluster
sudo systemctl stop arangodb3.service
sudo systemctl disable arangodb3.service
sudo systemctl mask arangodb3.service
