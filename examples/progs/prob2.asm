.data
prev_0: 1
prev_1: 0
prev_2: 0
curr_0: 1
curr_1: 0
curr_2: 0
next_0: 0
next_1: 0
next_2: 0
sum_0:  0
sum_1:  0
sum_2:  0
sum_3:  0
lim_0:  0
lim_1:  9
lim_2:  61
even_mask: 1
_0: 0

.text
main_loop:  call calc_next
check_lim:  ld   next_2
            cmp  lim_2
            jgt  finish
            jne  continue
            ld   next_1
            cmp  lim_1
            jgt  finish
            jne  continue
            ld   next_0
            cmp  lim_0
            jgt  finish

continue:   call add_next
            call mov_curr
            call mov_next
            jump main_loop
finish:     ld sum_2
            out
            ld sum_1
            out
            ld sum_0
            out
            hlt

calc_next:  ld  prev_0
            add curr_0
            st  next_0
            ld  prev_1
            adc curr_1
            st  next_1
            ld  prev_2
            adc curr_2
            st  next_2
            ret

add_next:   ld next_0
            and even_mask
            cmp _0
            jne skip
            ld  sum_0
            add next_0
            st  sum_0
            ld  sum_1
            adc next_1
            st  sum_1
            ld  sum_2
            adc next_2
            st  sum_2
            ld  sum_3
            adc _0
            st  sum_3
skip:       ret

mov_curr:   ld  curr_0
            st  prev_0
            ld  curr_1
            st  prev_1
            ld  curr_2
            st  prev_2
            ret

mov_next:   ld  next_0
            st  curr_0
            ld  next_1
            st  curr_1
            ld  next_2
            st  curr_2
            ret
