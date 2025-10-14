package main

import (
	"github.com/tuneinsight/lattigo/v6/core/rlwe"
	"github.com/tuneinsight/lattigo/v6/schemes/bgv"
)

func int2uint(val int64, t uint64) uint64 {
	temp := int64(val) % int64(t)
	if temp < 0 {
		temp += int64(t)
	}
	return uint64(temp)
}

func uint2int(val uint64, t uint64) int64 {
	temp := int64(val % t)
	
	if temp > int64(t/2) {
		temp -= int64(t)
	}

	return temp
}

func mem_update(new_one *rlwe.Ciphertext, io []*rlwe.Ciphertext) {
	for i := 0; i < 3; i++ {
		io[i] = io[i+1]
	}

	io[3] = new_one
}

func ctrl(eval *bgv.Evaluator, pg []*rlwe.Ciphertext, io []*rlwe.Ciphertext) *rlwe.Ciphertext {
	r_mul := make([]*rlwe.Ciphertext, 4)
	var r_sum *rlwe.Ciphertext
	var u_enc *rlwe.Ciphertext

	for i := 0; i < 4; i++ {
		r_mul[i], _ = eval.MulNew(pg[i], io[i])
	}

	r_sum = r_mul[0]

	for i := 1; i < 4; i++ {
		eval.Add(r_sum, r_mul[i], r_sum)
	}

	u_enc = r_sum
	r_sum, _ = eval.RotateColumnsNew(r_sum, 1)
	eval.Add(u_enc, r_sum, u_enc)
	r_sum, _ = eval.RotateColumnsNew(r_sum, 1)
	eval.Add(u_enc, r_sum, u_enc)

	return u_enc
}
