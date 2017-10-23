find snakes -name "*.ebnf" | while read EBNF
do
  TARGET=$(dirname $EBNF)/$(basename $EBNF .ebnf)parse.py
  if test "$EBNF" -nt "$TARGET"
  then
    echo "### $EBNF"
    tatsu -o $TARGET $EBNF
  else
    echo "... $EBNF"
  fi
done
