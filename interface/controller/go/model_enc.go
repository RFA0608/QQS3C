package main

import (
	"math"

	RGSW "github.com/CDSL-EncryptedControl/CDSL/utils/core/RGSW"
	RLWE "github.com/CDSL-EncryptedControl/CDSL/utils/core/RLWE"
	"github.com/tuneinsight/lattigo/v6/core/rgsw"
	"github.com/tuneinsight/lattigo/v6/core/rlwe"
	"github.com/tuneinsight/lattigo/v6/ring"
)

type crypto_context struct {
	params    *rlwe.Parameters
	levelQ    int
	levelP    int
	ringQ     *ring.Ring
	monomials []ring.Poly
	tau       int

	kgen *rlwe.KeyGenerator
	sk   *rlwe.SecretKey
	rlk  *rlwe.RelinearizationKey

	encryptorRLWE *rlwe.Encryptor
	decryptorRLWE *rlwe.Decryptor
	evaluatorRLWE *rlwe.Evaluator
	encryptorRGSW *rgsw.Encryptor
	evaluatorRGSW *rgsw.Evaluator
}

type info_enc struct {
	r float64
	s float64
	L float64

	params        *rlwe.Parameters
	ringQ         *ring.Ring
	monomials     []ring.Poly
	tau           int
	evaluatorRLWE *rlwe.Evaluator
	evaluatorRGSW *rgsw.Evaluator

	ctF []*rgsw.Ciphertext
	ctG []*rgsw.Ciphertext
	ctH []*rgsw.Ciphertext
	ctR []*rgsw.Ciphertext
}

func get_params() *rlwe.Parameters {
	params, _ := rlwe.NewParametersFromLiteral(rlwe.ParametersLiteral{
		LogN:    12,
		LogQ:    []int{60},
		LogP:    []int{60},
		NTTFlag: true,
	})

	return &params
}

func crypto(params *rlwe.Parameters) *crypto_context {
	// set parameters
	n := 4
	m := 1
	p := 2
	levelQ := params.QCount() - 1
	levelP := params.PCount() - 1
	ringQ := params.RingQ()

	// Compute tau
	// least power of two greater than n, p_, and m
	maxDim := math.Max(math.Max(float64(n), float64(m)), float64(p))
	tau := int(math.Pow(2, math.Ceil(math.Log2(maxDim))))

	// Generate DFS index for unpack
	dfsId := make([]int, tau)
	for i := 0; i < tau; i++ {
		dfsId[i] = i
	}

	tmp := make([]int, tau)
	for i := 1; i < tau; i *= 2 {
		id := 0
		currBlock := tau / i
		nextBlock := currBlock / 2
		for j := 0; j < i; j++ {
			for k := 0; k < nextBlock; k++ {
				tmp[id] = dfsId[j*currBlock+2*k]
				tmp[nextBlock+id] = dfsId[j*currBlock+2*k+1]
				id++
			}
			id += nextBlock
		}

		for j := 0; j < tau; j++ {
			dfsId[j] = tmp[j]
		}
	}

	// Generate monomials for unpack
	logn := int(math.Log2(float64(tau)))
	monomials := make([]ring.Poly, logn)
	for i := 0; i < logn; i++ {
		monomials[i] = ringQ.NewPoly()
		idx := params.N() - params.N()/(1<<(i+1))
		monomials[i].Coeffs[0][idx] = 1
		ringQ.MForm(monomials[i], monomials[i])
		ringQ.NTT(monomials[i], monomials[i])
	}

	// Generate Galois elements for unpack
	galEls := make([]uint64, int(math.Log2(float64(tau))))
	for i := 0; i < int(math.Log2(float64(tau))); i++ {
		galEls[i] = uint64(tau/int(math.Pow(2, float64(i))) + 1)
	}

	// Generate keys
	kgen := rlwe.NewKeyGenerator(params)
	sk := kgen.GenSecretKeyNew()
	rlk := kgen.GenRelinearizationKeyNew(sk)
	evkRGSW := rlwe.NewMemEvaluationKeySet(rlk)
	evkRLWE := rlwe.NewMemEvaluationKeySet(rlk, kgen.GenGaloisKeysNew(galEls, sk)...)

	// Define encryptor and evaluator
	encryptorRLWE := rlwe.NewEncryptor(params, sk)
	decryptorRLWE := rlwe.NewDecryptor(params, sk)
	evaluatorRLWE := rlwe.NewEvaluator(params, evkRLWE)
	encryptorRGSW := rgsw.NewEncryptor(params, sk)
	evaluatorRGSW := rgsw.NewEvaluator(params, evkRGSW)

	crypto_cl := crypto_context{
		params:        params,
		levelQ:        levelQ,
		levelP:        levelP,
		ringQ:         ringQ,
		monomials:     monomials,
		tau:           tau,
		kgen:          kgen,
		sk:            sk,
		rlk:           rlk,
		encryptorRLWE: encryptorRLWE,
		decryptorRLWE: decryptorRLWE,
		evaluatorRLWE: evaluatorRLWE,
		encryptorRGSW: encryptorRGSW,
		evaluatorRGSW: evaluatorRGSW,
	}

	return &crypto_cl
}

func enc_for_intmat(crypto_cl *crypto_context) *info_enc {
	F_q := [][]float64{
		{0, 0, 0, 0},
		{1, 0, 0, -2},
		{0, 1, 0, 1},
		{0, 0, 1, 2},
	}

	G_q := [][]float64{
		{1000, -1419},
		{0, -11490},
		{0, -5942},
		{0, 5723},
	}

	H_q := [][]float64{
		{69691, -5260, 152481, 142539},
	}

	R_q := [][]float64{
		{4},
		{-1422},
		{-718},
		{702},
	}

	ctF := RGSW.EncPack(F_q, crypto_cl.tau, crypto_cl.encryptorRGSW, crypto_cl.levelQ, crypto_cl.levelP, crypto_cl.ringQ, *crypto_cl.params)
	ctG := RGSW.EncPack(G_q, crypto_cl.tau, crypto_cl.encryptorRGSW, crypto_cl.levelQ, crypto_cl.levelP, crypto_cl.ringQ, *crypto_cl.params)
	ctH := RGSW.EncPack(H_q, crypto_cl.tau, crypto_cl.encryptorRGSW, crypto_cl.levelQ, crypto_cl.levelP, crypto_cl.ringQ, *crypto_cl.params)
	ctR := RGSW.EncPack(R_q, crypto_cl.tau, crypto_cl.encryptorRGSW, crypto_cl.levelQ, crypto_cl.levelP, crypto_cl.ringQ, *crypto_cl.params)

	enc4intmat := info_enc{
		r:             1000.0,
		s:             1000.0,
		L:             1000000.0,
		params:        crypto_cl.params,
		ringQ:         crypto_cl.ringQ,
		monomials:     crypto_cl.monomials,
		tau:           crypto_cl.tau,
		evaluatorRLWE: crypto_cl.evaluatorRLWE,
		evaluatorRGSW: crypto_cl.evaluatorRGSW,
		ctF:           ctF,
		ctG:           ctG,
		ctH:           ctH,
		ctR:           ctR,
	}

	return &enc4intmat
}

func intmat_state_update_enc(x_enc *rlwe.Ciphertext, y_enc *rlwe.Ciphertext, u_enc []*rlwe.Ciphertext, info *info_enc) *rlwe.Ciphertext {
	// Unpack state
	xCt := RLWE.UnpackCt(x_enc.CopyNew(), 4, info.tau, info.evaluatorRLWE, info.ringQ, info.monomials, *info.params)

	// Unpack input
	yCt := RLWE.UnpackCt(y_enc, 2, info.tau, info.evaluatorRLWE, info.ringQ, info.monomials, *info.params)

	// state update
	FxCt := RGSW.MultPack(xCt, info.ctF, info.evaluatorRGSW, info.ringQ, *info.params)
	GyCt := RGSW.MultPack(yCt, info.ctG, info.evaluatorRGSW, info.ringQ, *info.params)
	RuCt := RGSW.MultPack(u_enc, info.ctR, info.evaluatorRGSW, info.ringQ, *info.params)
	xCtPack := RLWE.Add(FxCt, GyCt, RuCt, *info.params)

	return xCtPack
}

func intmat_get_output_enc(x_enc *rlwe.Ciphertext, info *info_enc) *rlwe.Ciphertext {
	// Unpack state
	xCt := RLWE.UnpackCt(x_enc.CopyNew(), 4, info.tau, info.evaluatorRLWE, info.ringQ, info.monomials, *info.params)

	// get output
	uCtPack := RGSW.MultPack(xCt, info.ctH, info.evaluatorRGSW, info.ringQ, *info.params)

	return uCtPack
}
