find snakes -name "*.ebnf" | while read EBNF
do
  echo "### $EBNF"
  TARGET=$(dirname $EBNF)/$(basename $EBNF .ebnf)parse.py
  tatsu -o $TARGET $EBNF
done
