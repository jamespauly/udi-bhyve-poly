# AcuRite Access®

This is a node server to interface with an Acurite Access systems and make it available to a Universal Devices ISY994i Polyglot interface with Polyglot V3 running on a Polisy

Currently supports AcuRite Access® for Remote Monitoring and any device that can link to it.

### Installation
1. Backup Your ISY!
2. Go to the Polyglot Store in the UI and install.
3. From the Polyglot dashboard, select the Acurite node server.
4. Restart the Admin Console to properly display the new node server nodes.

### Notes
* The devices will not show up until you enter the user and password for the myacurite.com site.
* It can take a minute for the nodes to show any data.

### Custom Parameters Configuration
* <b>acurite_user</b> - myacurite.com username
* <b>acurite_password</b> - myacurite.com password

### Requirements
Here are the python modules required to use this node server:<BR>
* requests
* jsonpath-ng
