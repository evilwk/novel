package main

import (
	"novel"
)

func main() {
	n := novel.NewNovel("https://www.txtjia.com/yuedu/297884/")
	n.Start(&novel.TxtJia{})
}
