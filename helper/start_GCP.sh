#!/bin/bash

# set up env (path, etc.)
. ~/.bashrc

process=globusconnectpersonal
LOG_DIR=$HOME/logs


running "$process"
if [ $? = 1 ]; then
  echo "starting $process -start"
  $process -start 2>&1 | \
    LogFilter -d $LOG_DIR -p $process &
fi

