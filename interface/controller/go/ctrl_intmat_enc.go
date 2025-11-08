package main

import (
	"fmt"
	"time"

	tccp "github.com/RFA0608/QQS3C/go"

	utils "github.com/CDSL-EncryptedControl/CDSL/utils"
	RLWE "github.com/CDSL-EncryptedControl/CDSL/utils/core/RLWE"
)

const host = "localhost"
const port = "9999"

func main() {
	// set simulation
	run_signal := true

	// get crypto and controller model
	params := Get_params()
	crypto_cl := Crypto(params)
	info_enc := Enc_for_intmat(crypto_cl)

	// input/output initialization
	x_ini := []float64{
		0.0,
		0.0,
		0.0,
		0.0,
	}
	y := []float64{
		0.0,
		0.0,
	}
	u := []float64{
		0.0,
	}

	// set init encrypted state
	xBar := utils.RoundVec(utils.ScalVecMult((info_enc.r * info_enc.s), x_ini))
	xCtPack := RLWE.EncPack(xBar, info_enc.tau, info_enc.L, *crypto_cl.encryptorRLWE, info_enc.ringQ, *info_enc.params)

	conn := tccp.InitTCP(host, port)

	for run_signal {
		_, flag := tccp.Recv(conn)

		if flag.(string) == "run" {
			// start clock set
			stc := time.Now()

			// get plant output
			_, y0 := tccp.Recv(conn)
			_, y1 := tccp.Recv(conn)
			y[0] = y0.(float64)
			y[1] = y1.(float64)

			// send control input data
			tccp.Send(conn, u[0])

			// Quantize and encrypt
			yBar := utils.RoundVec(utils.ScalVecMult(info_enc.r, y))
			yCtPack := RLWE.EncPack(yBar, info_enc.tau, info_enc.L, *crypto_cl.encryptorRLWE, info_enc.ringQ, *info_enc.params)

			// Re-encrypt output
			uBar := utils.RoundVec(utils.ScalVecMult(info_enc.r, u))
			uReEnc := RLWE.Enc(uBar, info_enc.L, *crypto_cl.encryptorRLWE, info_enc.ringQ, *info_enc.params)

			// controller description //
			// ------------------------------------------------ //
			// state update on ciphertext
			xCtPack = Intmat_state_update_enc(xCtPack, yCtPack, uReEnc, info_enc)

			// get output on ciphertext
			uCtPack := Intmat_get_output_enc(xCtPack, info_enc)
			// ------------------------------------------------ //

			u = RLWE.DecUnpack(uCtPack, 1, info_enc.tau, *crypto_cl.decryptorRLWE, 1/(info_enc.r*info_enc.s*info_enc.s*info_enc.L), info_enc.ringQ, *info_enc.params)

			// end clock set
			edc := time.Now()
			duration := edc.Sub(stc)
			fmt.Printf("loop time: %dms\n", duration.Milliseconds())

			// ------------------------------------------------ //
		} else if flag.(string) == "end" {
			run_signal = false
			break
		}
	}

	tccp.ExitTCP(conn)
}
