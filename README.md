# EMSM

The **Extendable Minecraft Server Manager** (EMSM) is a minecraft server wrapper that is able to handle multiple minecraft worlds and server versions.

The **EMSM** itself provides only a simple but sufficient **API** to manage the worlds. The rest of the work is done by the plugins.


# Getting started

Please read the [online documentation](http://emsm.benediktschmitt.de) for a full introduction in the **EMSM**. The documentation is small and comprehensible.


## Environment

The **EMSM** requires *Python 3.2* or higher and *screen*. Furthermore, we need *java* to run the minecraft server, *tar* to extract the **EMSM** archive and *wget* to download it.

	$ apt-get update 
	$ apt-get install screen openjdk-7-jre-headless python3.2 tar wget

Create the user that should run the application:

	$ adduser minecraft --disabled-password --shell=/bin/false
      
Switch to the home directory of *minecraft*:

   	$ cd /home/minecraft
   
Download the application and extract it in the home directory of *minecraft*:

	$ wget https://github.com/benediktschmitt/emsm/archive/master.tar.gz
	$ tar -xzf master.tar.gz
	$ mv emsm-master/* ./
	$ rm -r emsm-master master.tar.gz
	$ chown -R minecraft:minecraft /home/minecraft
      
The **EMSM** and its subdirectories are now in the home directory of *minecraft*.

Copy the *bin_script* into the */usr/build* directory:
   
	$ cp emsm/bin_script /usr/bin/minecraft
	$ chmod +x /usr/bin/minecraft

Well, that's all. For the first run, type:

	$ minecraft

This will create the other subdirectories and the configuration files. If the *bin-script* does not work, take a look at the [documentation](http://emsm.benediktschmitt.de/how_to/index.html).


## Configuration

main.conf:
```ini
[emsm]
user = minecraft
```

server.conf:
```ini
[vanilla_1.6]
server = minecraft_server_1.6.jar
url = https://s3.amazonaws.com/Minecraft.Download/versions/1.6.2/minecraft_server.1.6.2.exe
start_args = nogui.
```

worlds.conf:
```ini
[foo]
port = 25565
server = vanilla_1.6
```   

To start the world *foo*, use the command:
	
	$ minecraft -p worlds -w foo --start

If the minecraft server has not been downloaded yet, it will be downloaded now. So don't worry if the script runs longer than expected.

   
## Commands

To perfom a dry-run, type:

	$ minecraft
   
If you need more help, use the **--help** argument:

	$ minecraft -h
	$ minecraft -h -p worlds
	$ minecraft -h -p server
	$ minecraft -h -p backups
	$ minecraft -h -p ...
  
  
# Versioning

The **EMSM** uses semantic version numbers. Take a look at http://semver.org/ for further information.
