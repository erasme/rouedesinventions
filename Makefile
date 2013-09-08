.PHONY: graphics release debug

graphics:
	make -C data/hd

release:
	buildozer android release

debug:
	buildozer android debug
