for CS in libs/js/*.cs
do
  coffe -c -m -o $(basename $CS .cs).js $CS
done
