#!/bin/bash


process="globusconnectpersonal"

full_process="globusconnectpersonal -start -dir $HOME/.globusonline"
LOG_DIR=$HOME/logs


globusconnectpersonal -status 
if [ $? = 1 ]; then
  echo "starting $full_process"
  $full_process 2>&1 | \
    LogFilter -d $LOG_DIR -p $process &
fi

