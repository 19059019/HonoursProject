str="submissions/wololo"
 
IFS='/' # space is set as delimiter
read -ra ADDR <<< "$str" # str is read into an array as tokens separated by IFS
echo ${ADDR[1]}
