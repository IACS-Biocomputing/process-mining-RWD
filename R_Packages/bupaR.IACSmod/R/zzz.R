

load <- c("edeaR.IACSmod", "eventdataR","processmapR.IACSmod","xesreadR", "processmonitR.IACSmod", "petrinetR")

.onAttach <- function(...) {
	needed <- load[!is_attached(load)]

	if (length(needed) == 0)
		return()

	needed_installed <- ((sapply(needed, require, character.only = TRUE, warn.conflicts = FALSE)))

	# no_installed <- needed[!needed_installed]
	#
	# if(length(no_installed) > 0) {
	# 	packageStartupMessage(paste0("bupaR works best with the following package(s) installed: ", toString(no_installed),
	# 								 ". \nDo you want to install these?\n"))
	# 	answer <- readline("Y/N: ")
	#
	# 	if(answer == "Y"){
	# 		map(no_installed, ~install.packages(.x))
	# 	}
	#
	# 	if(answer == "Y"){
	# 		suppressWarnings(suppressPackageStartupMessages(sapply(no_installed, require, character.only = TRUE, warn.conflicts = FALSE)))
	# 	}
	# }


}

is_attached <- function(x) {
	paste0("package:", x) %in% search()
}
