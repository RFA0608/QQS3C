// The folder with go.mod must have the file "tcp_protocol_client.go" with the same package name
package protocol

import "fmt"

const host = "localhost"
const port = "9999"

func main() {
	conn := InitTCP(host, port)

	_, data := Recv(conn)
	fmt.Print("recv : ")
	fmt.Println(data)
	Send(conn, data.(int64))

	_, data = Recv(conn)
	fmt.Print("recv : ")
	fmt.Println(data)
	Send(conn, data.(float64))

	_, data = Recv(conn)
	fmt.Print("recv : ")
	fmt.Println(data)
	Send(conn, data.(string))

	ExitTCP(conn)
}
