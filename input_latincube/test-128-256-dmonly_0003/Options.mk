MPICC = mpicc
MPICXX = mpic++
OPTIMIZE = -fopenmp -O3 -g -Wall -ffast-math -march=corei7
GSL_INCL = $(shell gsl-config --cflags)
GSL_LIBS = $(shell gsl-config --libs)
