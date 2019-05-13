# GlobusArchiver
Python utility to archive local data via Globus (originally designed for the Campaign Store), but could be used with
any globus endpoint.

## Requires
Python 3
ConfigMaster  (installed via manage_externals -- see instructions below)

# Installing the Globus CLI, globusconnectpersonal

You will need these installed to start your own local endpoint.  I had SNAT install them in:
* /opt/globusconnectpersonal-2.3.6/globusconnectpersonal
* /opt/bin/globus

The instructions that follow assume these two programs are in your path.

# Installing the Globus Python SDK
To run GlobusArchiver.py, you will need the Globus Python SDK installed.

As long as you have write permissions in your python3 environment, you can install it yourself using pip.  INstructions online are straightforward:
https://globus-sdk-python.readthedocs.io/en/stable/installation/


# Installing GlobusArchiver

After you have cloned the GlobusArchiver repository, you can run checkout_externals to get any external dependencies:

To get the required dependencies, run the following:
./manage_externals/checkout_externals


# Using the GlobusArchiver

## Configure your local accesible directories

You will need to edit ~/.globusonline/lta/config-paths to configure which local directories are accessible on your personal endpoint.  Instructions online here:
https://docs.globus.org/faq/globus-connect-endpoints/#how_do_i_configure_accessible_directories_on_globus_connect_personal_for_linux

## Create your local endpoint
```
# set this to whatever you want - I am using the name of the machine I am on.
export LOCAL_EP_NAME=$(uname -n)

globus login --no-local-server
globus endpoint create --personal $LOCAL_EP_NAME > local_endpoint.log

# get local setup ID, and local endpoint ID
export LOCAL_SETUP_ID=$(grep Setup endpoint.log | rev | cut -f1 -d' ' | rev)
export LOCAL_EP_ID=$(globus endpoint search '$LOCAL_EP_NAME' | grep $LOCAL_EP_NAME | cut -f1 -d' ')

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
First you will want to use the "print_params" argument to create a default configuration file for GlobusArchiver.py

```
GlobusArchiver.py --print_params > GlobusArchiver_my_project.py
```

Now edit your configuration file.  You will likely need to edit the ...

