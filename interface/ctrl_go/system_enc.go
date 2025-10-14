package main

import (
	"fmt"
	"math"
	"os"
	"time"

	"github.com/tuneinsight/lattigo/v6/core/rlwe"
	"github.com/tuneinsight/lattigo/v6/ring"
	"github.com/tuneinsight/lattigo/v6/schemes/bgv"
)

const host = "localhost"
const port = "9999"

func main() {
	var r float64 = 1000
	var s float64 = 1000

	pq := [][]float64{
		{-13.3443203999253, 15.0030518107562, -0.0227503562486410},
		{69.7255986973738, -81.7399354434618, 0.145231734991849},
		{-107.639518675920, 147.752435602488, -0.505904999998477},
		{51.6633130000854, -88.1602769609419, 0.492475989578353},
	}

	pq_q := [][]uint64{
		{0, 0, 0},
		{0, 0, 0},
		{0, 0, 0},
		{0, 0, 0},
	}

	pq_c := make([]*rlwe.Ciphertext, 4)
	io_c := make([]*rlwe.Ciphertext, 4)

	logN := 13
	ptSize := uint64(24)
	ctSize := []int{42, 42, 42}

	primeGen := ring.NewNTTFriendlyPrimesGenerator(ptSize, uint64(math.Pow(2, float64(logN)+1)))
	ptModulus, _ := primeGen.NextAlternatingPrime()
	logQ := ctSize

	params, _ := bgv.NewParametersFromLiteral(bgv.ParametersLiteral{
		LogN:             logN,
		LogQ:             logQ,
		PlaintextModulus: ptModulus,
	})

	kgen := bgv.NewKeyGenerator(params)
	sk := kgen.GenSecretKeyNew()

	rlk := kgen.GenRelinearizationKeyNew(sk)

	rots := []uint64{params.GaloisElementForColRotation(+1), params.GaloisElementForColRotation(+2)}
	rotkeys := kgen.GenGaloisKeysNew(rots, sk)

	evk := rlwe.NewMemEvaluationKeySet(rlk, rotkeys...)

	encryptor := bgv.NewEncryptor(params, sk)
	decryptor := bgv.NewDecryptor(params, sk)
	encoder := bgv.NewEncoder(params)
	eval := bgv.NewEvaluator(params, evk)


	var u_c *rlwe.Ciphertext
	u_p := bgv.NewPlaintext(params, params.MaxLevel())
	u_d := make([]uint64, params.MaxSlots())

	var sample_time float64 = 20
	var conn_margin float64 = 0.25
	var state int = 1
	var y0 float64 = 0.0
	var y1 float64 = 0.0
	var u float64 = 0.0
	var stc time.Time
	var edc time.Time
	var duration time.Duration
	var run_time int64
	var EoL bool = true

	pod_matrix := make([]uint64, params.MaxSlots())
	sampled_data_p := bgv.NewPlaintext(params, params.MaxLevel())
	t := params.PlaintextModulus()
	var sampled_data_c *rlwe.Ciphertext

	for i := 0; i < 4; i++ {
		for j := 0; j < 3; j++ {
			pq_q[i][j] = int2uint(int64(pq[i][j] * s), t)
		}
	}

	for i := 0; i < 4; i++ {
		pod_matrix[0] = pq_q[i][0]
		pod_matrix[1] = pq_q[i][1]
		pod_matrix[2] = pq_q[i][2]
		encoder.Encode(pod_matrix, sampled_data_p)
		pq_c[i], _ = encryptor.EncryptNew(sampled_data_p)

		pod_matrix[0] = 0
		pod_matrix[1] = 0
		pod_matrix[2] = 0
		encoder.Encode(pod_matrix, sampled_data_p)
		io_c[i], _ = encryptor.EncryptNew(sampled_data_p)
	}

	conn := InitTCP(host, port)
	var flag any
	var data any

	for EoL {
		if state == 1 {
			_, flag = Recv(conn)

			switch flag.(string) {
			case "R":
				stc = time.Now()

				Send(conn, "ITR")
				_, data = Recv(conn)
				y0 = data.(float64)
				_, data = Recv(conn)
				y1 = data.(float64)
				Send(conn, u)

				fmt.Printf("y0: %f | y1: %f | u: %f\n", y0, y1, u)

				state = 2
			case "E":
				EoL = false
			default:
				os.Exit(-1)
			}
		} else if state == 2 {
			_, flag = Recv(conn)

			switch flag.(string) {
			case "R":
				Send(conn, "W")

				pod_matrix[0] = uint64(int2uint(int64(y0 * r), t))
				pod_matrix[1] = uint64(int2uint(int64(y1 * r), t))
				pod_matrix[2] = uint64(int2uint(int64(u * r), t))

				encoder.Encode(pod_matrix, sampled_data_p)
				sampled_data_c, _ = encryptor.EncryptNew(sampled_data_p)

				u_c = ctrl(eval, pq_c, io_c)
				io_c = mem_update(sampled_data_c, io_c)

				decryptor.Decrypt(u_c, u_p)
				encoder.Decode(u_p, u_d)

				u = float64(uint2int(u_d[0], t)) / r / s

				state = 3
			case "E":
				EoL = false
			default:
				os.Exit(-1)
			}

		} else if state == 3 {
			_, flag = Recv(conn)

			switch flag.(string) {
			case "R":
				edc = time.Now()
				duration = edc.Sub(stc)
				run_time = duration.Microseconds()

				if float64(run_time)/1000 < (sample_time - conn_margin) {
					Send(conn, "W")
				} else {
					Send(conn, "W")
					fmt.Printf("sampled_period: %fms\n", float64(run_time)/1000)
					state = 1
					break
				}
			case "E":
				EoL = false
			default: 
				os.Exit(-1)
			}
		} else {
			os.Exit(-1)
		}
	}

	ExitTCP(conn)
}
