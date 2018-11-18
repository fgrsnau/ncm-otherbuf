if get(s:, 'loaded', 0)
    finish
endif
let s:loaded = 1

let g:ncm2_otherbuf#proc = yarp#py3({
    \ 'module': 'ncm2_otherbuf',
    \ 'on_load': { -> ncm2#set_ready(g:ncm2_otherbuf#source)}
    \ })

let g:ncm2_otherbuf#source = extend(get(g:, 'ncm2_otherbuf#source', {}), {
            \ 'name': 'otherbuf',
            \ 'ready': 0,
            \ 'priority': 4,
            \ 'mark': 'o',
            \ 'on_complete': 'ncm2_otherbuf#on_complete',
            \ 'on_warmup': 'ncm2_otherbuf#on_warmup',
            \ }, 'keep')

func! ncm2_otherbuf#init()
    call ncm2#register_source(g:ncm2_otherbuf#source)

    augroup ncm2_otherbuf
        au! BufAdd    * call ncm2_otherbuf#on_event('BufAdd')
        au! BufDelete * call ncm2_otherbuf#on_event('BufDelete')
        au! BufLeave  * call ncm2_otherbuf#on_event('BufLeave')
    augroup END
endfunc

func! ncm2_otherbuf#on_warmup(ctx)
    call g:ncm2_otherbuf#proc.jobstart()
endfunc

func! ncm2_otherbuf#on_complete(ctx)
    call g:ncm2_otherbuf#proc.try_notify('on_complete', a:ctx)
endfunc

func! ncm2_otherbuf#on_event(event)
    call g:ncm2_otherbuf#proc.try_notify('on_event', a:event, bufnr('%'))
endfunc

