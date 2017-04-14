" Defines the highlighting for the header section, the content is plain
" MarkDown with its own syntax.


" Define some keywords for the headers
syntax keyword headerKeyword id title status categories tags containedin=headerLabel
highlight link headerKeyword Keyword
syntax keyword headerHead wordpress containedin=headerSection
highlight link headerHead Constant
syntax keyword headerFieldKeyword draft published containedin=headerIni
highlight link headerFieldKeyword Constant

" Header section highlighting
syntax match headerSection /\[.*\]$/ containedin=headerIni
highlight link headerSection Special
syntax match headerLabel /.*=/ containedin=headerIni contains=headerComment
highlight link headerLabel Type
syntax match headerComment /^[#;].*$/ containedin=headerIni
syntax match headerComment /[;].*$/ containedin=headerIni
highlight link headerComment Comment

syntax region headerIni start='\[wordpress]$' end="---$"me=s-1 contains=@Spell


" Markdown syntax for the content
syntax include @MD syntax/markdown.vim
syntax region contentMarkdown start="---$" end="\%$" contains=@MD,@Spell
