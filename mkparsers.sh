#find zinc -name "*.lark" | while read LARK
#do
#  TARGET=$(dirname $LARK)/$(basename $LARK .lark)parse.py
#  if test "$LARK" -nt "$TARGET"
#  then
#    echo "### $LARK"
#    python -m lark.tools.standalone "$LARK" > "$TARGET"
#  else
#    echo "... $LARK"
#  fi
#done

find zinc -name "*.ebnf" | while read EBNF
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

find zinc -name "*_peg.py" | while read PEG
do
  TARGET=$(dirname $PEG)/$(basename $PEG _peg.py)parse.py
  CNAME=$(grep 'class.*(fastidious\.Parser)' "$PEG" | awk '{print $2}')
  CPATH=$(realpath $PEG | sed -e "s|$(pwd)/*\(.*\).py|\\1|" -e "s|/|.|g")
  if test "$PEG" -nt "$TARGET" || ! test -f "$TARGET"
  then
    echo "### $PEG ($CPATH.$CNAME)"
    fastidious generate -o $TARGET $CPATH.$CNAME
  else
    echo "... $PEG ($CPATH.$CNAME)"
  fi
done
