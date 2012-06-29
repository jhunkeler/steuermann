" To use syntax highlighting with vim:
"
" put this file in ~/.vim/syntax/steuermann.vim
"
" put this command in ~/.vimrc
"	autocmd BufRead,BufNewFile  *.sm        set filetype=steuermann

syntax match Comment "#.*$"

syntax keyword Keyword HOSTGROUP TABLE HOST CMD OPT AFTER RUN LOCAL
syntax keyword Keyword IMPORT DEBUG 

syntax match IfClause "IF[^:]*:"

highlight IfClause guifg=green ctermfg=2

syntax match String  "\"[^"]*\""

syntax region PreProc start="CONDITIONS" end="[\s]*END[ \t]*\n"

syntax sync fromstart

