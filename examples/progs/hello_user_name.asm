.data
curr_sym_ptr: 0
last_sym_ptr: 0

str1_ptr: 'Hello, '
str2_ptr: '!'


.text
main:   ld    str1_ptr
        call  print
        call  io
        ld    str2_ptr
        call  print
        hlt

io:      in
         out
         jiu io_stop
         jump io
io_stop: ret

print:  st    curr_sym_ptr
        add  ~curr_sym_ptr
        st    last_sym_ptr
p_loop: ld    curr_sym_ptr
        inc
        st    curr_sym_ptr
        cmp   last_sym_ptr
        jgt   exit_l
        ld   ~curr_sym_ptr
        out
        jump  p_loop
exit_l: ret