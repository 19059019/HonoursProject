logs=$(ls|grep log);
for f in submissions/*;
    do
        IFS='/'; # space is set as delimiter
        read -ra ADDR <<< "$f"; # str is read into an array as tokens separated by IFS
        filename=${ADDR[1]};
        log_file=$"../../${logs}/${filename}.txt";
        # Move to submission dir
        f="${ADDR[0]}/${ADDR[1]}"
		echo "${ADDR[0]}/${ADDR[1]}"
		echo $f;
		cd $f;
        # Actuall mark submission
        timeout 2 python marking.py &> $log_file;
        exit_code=$?;
        if [ $exit_code -eq 124 ]; then
            echo "************\
              MARKING SCRIPT TIMEOUT\
              ************" >> $log_file; fi;
        # Move back to source dir
        cd ../../;
    done
