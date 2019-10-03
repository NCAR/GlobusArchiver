# GlobusArchiver
Python utility to archive local data via Globus (originally designed for the Campaign Store), but could be used with
any globus endpoint.  GlobusArchiver.py is in the [Alpha phase](https://en.wikipedia.org/wiki/Software_release_life_cycle#Alpha), and is ready for experimentation by early-adopters. A beta release is planned for the end of June.

**NOTE: Instructions assume bash shell**

## Requires
* Python 3.6 or greater
* ConfigMaster  (installed via manage_externals -- see instructions below)
* A personal globus account

# Creating a Globus Account
You can find [instructions for creating a personal globus account on the CISL website](https://www2.cisl.ucar.edu/resources/storage-and-file-systems/globus-file-transfers).  

# Installing

## Installing the Globus CLI and globusconnectpersonal
The Globus CLI is available via the /usr/local anaconda install:
```
/usr/local/anaconda3/bin/globus
```

If you have a conda installation (e.g. on a mac), you can install like this:
```
conda config --add channels conda-forge
conda install globus-sdk
conda install globus-cli
```


You will need globusconnectpersonal installed to start your own local endpoint.  I had SNAT install it in:
* /opt/globusconnectpersonal


The instructions that follow assume these two programs are in your path.  

Here is one way you can add the globus CLI, globus SDK and globusconnectpersonal to your path.

```
echo export PATH=/usr/local/anaconda3/bin:\$PATH:/opt/globusconnectpersonal > ~/.globus_env
```
now you can source this file to set your environment
```
. ~/.globus_env
```
or add it to your .bashrc so your path is always set.

A "quickstart guide" to using Globus Connect Personal is given below, but you can also find more [information about Globus Connect Personal online](https://www.globus.org/globus-connect-personal).

## Installing the Globus Python SDK
To run GlobusArchiver.py, you will need the Globus Python SDK installed.

As long as you have write permissions in your python3 environment, you can install it yourself using pip.  Instructions online are straightforward:
https://globus-sdk-python.readthedocs.io/en/stable/installation/

## Keeping the Campaign Store Endpoint Active
By default the Campaign Store is only active for 24 hours.  You can extend this to 30 days.  First request a certificate by following the instructions on this [CISL web page](https://www2.cisl.ucar.edu/resources/storage-and-file-systems/configuring-globus-unattended-workflows).

When you run the gcert command, part of the output will say something like:
```
Globus certificate created in /glade/u/home/prestop!
```

look in that directory, and you will find a file named something like `.prestop-globus.cert`

To make globus available on cheyenne run:
```
module load python
ncar_pylib
```

Now you can activate your endpoint for 30 days.

```
globus endpoint activate --delegate-proxy /glade/u/home/prestop/.prestop-globus.cert --proxy-lifetime 720 6b5ab960-7bbf-11e8-9450-0a6d4e044368
```

You can confirm the 30 day expiration of your endpoint with this command:
```
globus endpoint activate 6b5ab960-7bbf-11e8-9450-0a6d4e044368`
```


## Installing GlobusArchiver

After you have cloned the GlobusArchiver repository, you can run checkout_externals to get any external dependencies:

To get the required dependencies, run the following:
```
./manage_externals/checkout_externals
```

# Using the GlobusArchiver

## Configure your local accesible directories

You will need to edit ~/.globusonline/lta/config-paths to configure which local directories are accessible via your personal endpoint.  If you are using GlobusArchiver to create TAR files, be sure to include your tmp directory in this file, because this is where tar files will be staged before sending.   [Details are online.](https://docs.globus.org/faq/globus-connect-endpoints/#how_do_i_configure_accessible_directories_on_globus_connect_personal_for_linux)

## Create your local endpoint
You only need to do this once.  Once you have your local endpoint created it persists.  You can check to see if you have a global endpoint already using the globus endpoint search:
```
globus endpoint search --filter-scope my-endpoints
```

You need to "create", "setup" and then "start" your endpoint:
```
# set this to whatever you want - I am using the name of the machine I am on.
export LOCAL_EP_NAME=$(uname -n)

globus login --no-local-server

# storing this output in a log file for ease of grepping later
globus endpoint create --personal $LOCAL_EP_NAME > local_endpoint.log

# get local setup ID, and local endpoint ID
export LOCAL_SETUP_ID=$(grep Setup local_endpoint.log | rev | cut -f1 -d' ' | rev)
export LOCAL_EP_ID=$(globus endpoint search $LOCAL_EP_NAME | grep $LOCAL_EP_NAME | cut -f1 -d' ')

# setup local personal endpoint
globusconnectpersonal  -setup $LOCAL_SETUP_ID
 
# start the GCP server
globusconnectpersonal -start &
```

You can check that your local endpoint is working:
```
globus ls ${LOCAL_EP_ID}:/path/to/local/files
```

## Running GlobusArchiver.py
If you used Archiver.pl in the past, you can use Archiver2GA.py (found in the helper subdirectory), to convert your old Archiver.pl configuration files to GlobusArchiver.py configuration files.

First you will want to use the "print_params" argument to create a default configuration file for GlobusArchiver.py   ConfigMaster treats your configuration file like a python module, and python requires no periods in the configuration name (except the .py), so **please use underscore or dash as separators in your configuration name.**

```
GlobusArchiver.py --print_params > GlobusArchiver_my_project.py
```

Now edit your configuration file.  You will likely need to edit the archive-items dictionary.

Finally run GlobusArchiver.py with your configuration file.  The first time you run GlobusArchiver.py, I recommmend you run interactively from the command line, and redirect the log to a file.  This will help keep debug and status message from obscuring prompts for authentication.

```
GlobusArchiver.py -c GlobusArchiver_my_project.py -l MyArchive.log -d DEBUG
```

You will probably get prompted to both authenticate your globus account and activate with the Campaign Store endpoint.  Once you do this the first time, you should not need to do it for 6 months.

