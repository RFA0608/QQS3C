import model
import model_enc

ctrl = model.ctrl(0.02)
ctrl_arx = model.ctrl_arx(ctrl.F, ctrl.G, ctrl.H, ctrl.J)
ctrl_arx_q = model.ctrl_arx_q(ctrl_arx.HG, ctrl_arx.HL)
ctrl_arx_q.set_level(10, 10)
ctrl_arx_q.quantize()
ctrl_arx_q.get_output()

enc = model_enc.crypto()
arec = model_enc.enc_for_system(enc, ctrl_arx_q.HG_q, ctrl_arx_q.HL_q)