// package main

// import (
// 	"encoding/csv"
// 	"fmt"
// 	"os"
// 	"time"

// 	tccp "github.com/RFA0608/QQS3C/communication/go/tpc"

// 	utils "github.com/CDSL-EncryptedControl/CDSL/utils"
// 	RLWE "github.com/CDSL-EncryptedControl/CDSL/utils/core/RLWE"
// )

// const host = "localhost"
// const port = "9999"

// func main() {
// 	// set simulation
// 	run_signal := true

// 	csv_file, err := os.Create("timing_log.csv")
// 	if err != nil {
// 		panic(err)
// 	}
// 	defer csv_file.Close()

// 	csv_writer := csv.NewWriter(csv_file)
// 	defer csv_writer.Flush()

// 	err = csv_writer.Write([]string{
// 		"whole_us",
// 		"y_enc_us",
// 		"u_re_enc_us",
// 		"state_update_us",
// 		"get_output_us",
// 		"u_dec_us",
// 		"theta(base)",
// 		"alpha(pendulum)",
// 		"u(input)",
// 	})
// 	if err != nil {
// 		panic(err)
// 	}

// 	// get crypto and controller model
// 	params := Get_params()
// 	crypto_cl := Crypto(params)
// 	info_enc := Enc_for_intmat(crypto_cl)

// 	// input/output initialization
// 	x_ini := []float64{
// 		0.0,
// 		0.0,
// 		0.0,
// 		0.0,
// 	}
// 	y := []float64{
// 		0.0,
// 		0.0,
// 	}
// 	u := []float64{
// 		0.0,
// 	}

// 	// set init encrypted state
// 	xBar := utils.RoundVec(utils.ScalVecMult((info_enc.r * info_enc.s), x_ini))
// 	xCtPack := RLWE.EncPack(xBar, info_enc.tau, info_enc.L, *crypto_cl.encryptorRLWE, info_enc.ringQ, *info_enc.params)

// 	conn := tccp.InitTCP(host, port)

// 	for run_signal {
// 		_, flag := tccp.Recv(conn)

// 		if flag.(string) == "run" {
// 			// start clock set
// 			stc := time.Now()

// 			// get plant output
// 			_, y0 := tccp.Recv(conn)
// 			_, y1 := tccp.Recv(conn)
// 			y[0] = y0.(float64)
// 			y[1] = y1.(float64)

// 			// send control input data
// 			tccp.Send(conn, u[0])

// 			// Quantize and encrypt
// 			stc_y_enc := time.Now()
// 			yBar := utils.RoundVec(utils.ScalVecMult(info_enc.r, y))
// 			yCtPack := RLWE.EncPack(yBar, info_enc.tau, info_enc.L, *crypto_cl.encryptorRLWE, info_enc.ringQ, *info_enc.params)
// 			edc_y_enc := time.Now()

// 			// Re-encrypt output
// 			stc_u_re_enc := time.Now()
// 			uBar := utils.RoundVec(utils.ScalVecMult(info_enc.r, u))
// 			uReEnc := RLWE.Enc(uBar, info_enc.L, *crypto_cl.encryptorRLWE, info_enc.ringQ, *info_enc.params)
// 			edc_u_re_enc := time.Now()

// 			// controller description //
// 			// ------------------------------------------------ //
// 			// state update on ciphertext
// 			stc_state_update := time.Now()
// 			xCtPack = Intmat_state_update_enc(xCtPack, yCtPack, uReEnc, info_enc)
// 			edc_state_update := time.Now()

// 			// get output on ciphertext
// 			stc_get_output := time.Now()
// 			uCtPack := Intmat_get_output_enc(xCtPack, info_enc)
// 			edc_get_output := time.Now()
// 			// ------------------------------------------------ //

// 			stc_u_dec := time.Now()
// 			u = RLWE.DecUnpack(uCtPack, 1, info_enc.tau, *crypto_cl.decryptorRLWE, 1/(info_enc.r*info_enc.s*info_enc.s*info_enc.L), info_enc.ringQ, *info_enc.params)
// 			edc_u_dec := time.Now()

// 			// end clock set
// 			edc := time.Now()
// 			duration_whole := edc.Sub(stc)
// 			duration_y_enc := edc_y_enc.Sub(stc_y_enc)
// 			duration_u_re_enc := edc_u_re_enc.Sub(stc_u_re_enc)
// 			duration_state_update := edc_state_update.Sub(stc_state_update)
// 			duration_get_output := edc_get_output.Sub(stc_get_output)
// 			duration_u_dec := edc_u_dec.Sub(stc_u_dec)

// 			fmt.Printf("%.3f,%.3f,%.3f,%.3f,%.3f,%.3f\n",
// 				float64(duration_whole.Nanoseconds())/1000.0,
// 				float64(duration_y_enc.Nanoseconds())/1000.0,
// 				float64(duration_u_re_enc.Nanoseconds())/1000.0,
// 				float64(duration_state_update.Nanoseconds())/1000.0,
// 				float64(duration_get_output.Nanoseconds())/1000.0,
// 				float64(duration_u_dec.Nanoseconds())/1000.0,
// 			)

// 			err = csv_writer.Write([]string{
// 				fmt.Sprintf("%.3f", float64(duration_whole.Nanoseconds())/1000.0),
// 				fmt.Sprintf("%.3f", float64(duration_y_enc.Nanoseconds())/1000.0),
// 				fmt.Sprintf("%.3f", float64(duration_u_re_enc.Nanoseconds())/1000.0),
// 				fmt.Sprintf("%.3f", float64(duration_state_update.Nanoseconds())/1000.0),
// 				fmt.Sprintf("%.3f", float64(duration_get_output.Nanoseconds())/1000.0),
// 				fmt.Sprintf("%.3f", float64(duration_u_dec.Nanoseconds())/1000.0),
// 				fmt.Sprintf("%.15f", y[0]),
// 				fmt.Sprintf("%.15f", y[1]),
// 				fmt.Sprintf("%.15f", u[0]),
// 			})
// 			if err != nil {
// 				panic(err)
// 			}

// 			csv_writer.Flush()
// 			if err := csv_writer.Error(); err != nil {
// 				panic(err)
// 			}

// 			// ------------------------------------------------ //
// 		} else if flag.(string) == "end" {
// 			run_signal = false
// 			break
// 		}
// 	}

// 	tccp.ExitTCP(conn)
// }
