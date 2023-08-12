# writing SLHD into files
library(SLHD)

set.seed(1)

t <- 1 # number of slices
m <- 10 # number of samples per slice
k <- 11 # number of parameters per sample
#Maximin-distance sliced Latin hypercube designs
D2<-maximinSLHD(t = t, m = m, k = k) 

D2$StandDesign

filename <- paste0("SLHD_t",t,"_m",m,"_k",k,".csv")

write.csv(D2$StandDesign, file = filename, row.names = FALSE)
