filter_trace_frequency_min_coverage <- function(eventlog,
												min_coverage,
												reverse){

	relative <- NULL

	eventlog %>%
		trace_coverage("case") %>%
		filter(relative >= min_coverage) %>%
		pull(1) -> case_selection

	filter_case(eventlog, case_selection, reverse)

}
