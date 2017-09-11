#!/bin/bash
#defined file paths
CURRENT_DIR=$pwd
SCRIPT_DIR=$(dirname $0)
RUN_SCRIPT=EOL.py
LIB_DIR=/etc/init.d
SERVICE=stinger-EOL
now=$(date +"%%Y-%m-%d_%H-%M-%N")

#Main script
if [ -e $LIB_DIR/$SERVICE ]; then
	echo "Service existed in systemd directory...proceed to modify"
	update-rc.d $SERVICE remove
	rm $LIB_DIR/$SERVICE
else
	echo "No Service found in system directory..."
fi

if [ -e $SCRIPT_DIR/$SERVICE ]; then
	echo "Enable services..."
	chmod 555 $SCRIPT_DIR/$RUN_SCRIPT
	dos2unix $SCRIPT_DIR/$RUN_SCRIPT
	dos2unix $SCRIPT_DIR/$SERVICE
	cp $SCRIPT_DIR/$SERVICE $LIB_DIR/
	chkconfig -add $SERVICE
else
	echo "No main or service found"
fi


