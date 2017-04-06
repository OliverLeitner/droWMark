function! PostWordPress()
    " Prepare arguments for python script.
    if( has('python') )
        let inter='python'
        let interfile='pyfile'
    else
        return "No python interpreter"
    endif
    exe inter . ' ' .'import vim'
    exe inter . ' ' .'import sys'
    let l:script = escape(s:path, ' ') . '/drowmark.py'
    exe inter.' ' . 'sys.argv = [ vim.eval("l:script"), vim.eval("@%") ]'
    " Call script
    exe interfile .' ' . l:script
endfunction

function! NewWordPress()
    let l:template = escape(s:path, ' ') . '/../templates/drowmark.template'
    exec 'read '. l:template
    setlocal ft=drowmark
endfunction

" Get a list of blog entries from our blog
function! ListWordPress()
    silent execute '!clear'
    let l:bloglist = '!python -c "import sys; import os; sys.path.append(os.path.abspath(\"'.s:path.'\")); import drowmark as dwm; dwm.getAllPosts(0,20)"'
    execute l:bloglist
    "exec 'read '. l:bloglist
    "setlocal buftype=nofile
endfunction

"publish an existing post
function! PublishWordPress()
    call inputsave()
    let l:postid = input('Enter a post ID to publish: ')
    call inputrestore()
    let l:publish = '!python -c "import sys; import os; sys.path.append(os.path.abspath(\"'.s:path.'\")); import drowmark as dwm; dwm.publishPost('.l:postid.')"'
    execute l:publish
endfunction

"update an existing post to db
function! UpdateWordPress()
    silent! exec 'write '.s:tmp.'/updatePost'
    silent! exec 'close'
    let l:update = 'python -c "import sys; import os; sys.path.append(os.path.abspath(\"'.s:path.'\")); import drowmark as dwm; dwm.updatePost(\"'.s:tmp.'/updatePost\")"'
    let l:tmpname = system(l:update)
    silent! exec '!rm -f '.s:tmp.'/updatePost'
    exec '!rm -f '.s:tmp.'/vwp_edit*'.l:tmpname
endfunction!

"edit an existing post
function! EditWordPress()
    call inputsave()
    let l:postid = input('Enter a post ID to edit: ')
    call inputrestore()
    let l:buffer = 'python -c "import sys; import os; sys.path.append(os.path.abspath(\"'.s:path.'\")); import drowmark as dwm; dwm.editPost('.l:postid.')"'
    let l:name = system(l:buffer)
    if winnr() > 1
        exec 'read '. l:name
    else
        exec 'vertical new'. l:name
        exec 'vertical resize +60'
    endif
    setlocal ft=drowmark
endfunction

"delete an existing post
function! DeleteWordPress()
    call inputsave()
    let l:postid = input('Enter a post ID to delete: ')
    call inputrestore()

    let l:delete = '!python -c "import sys; import os; sys.path.append(os.path.abspath(\"'.s:path.'\")); import drowmark as dwm; dwm.deletePost('.l:postid.')"'
    execute l:delete
endfunction

let s:tmp = ''
let s:os = system('echo $OSTYPE')

"im only running gnu, more to come, options are
"linux-gnu, darwin, cygwin, msys, win32, freebsd and more...
if s:os =~ 'linux-gnu'
    let s:tmp = escape('/tmp','\')
endif

let s:path = escape(resolve(expand('<sfile>:p:h')),'\')

command! ListWordPress call ListWordPress()
command! PublishWordPress call PublishWordPress()
command! UpdateWordPress call UpdateWordPress()
command! EditWordPress call EditWordPress()
command! DeleteWordPress call DeleteWordPress()
command! NewWordPress call NewWordPress()
command! PostWordPress call PostWordPress()
