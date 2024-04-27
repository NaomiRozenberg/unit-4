x = Array of numbers from 1 to 7 in random order
flips = True 
while flips: 
  flips = False
  loop i from 0 to length(x)-2
    if x[i] > [i+1]
      temp = x[i]
      x[i] = x[i+1] 
      flips = True 
    end if 
  end loop 
