#!/bin/env bash

# get my environment
. $HOME/.bashrc
# 
process=globusconnectpersonal
LOG_DIR=$HOME/logs

#param_file=$process.$instance

#cd $PROJ_DIR/model/params

running "$process"
if [ $? = 1 ]; then
  echo "starting $process -start"
  $process -start 2>&1 | \
    LogFilter -d $LOG_DIR -p $process &
fi

