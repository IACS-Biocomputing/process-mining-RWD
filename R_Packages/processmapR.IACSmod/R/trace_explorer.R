

#' @title Trace explorer
#' @description Explore traces, ordered by relative trace frequency
#' @param eventlog Eventlog object
#' @param type Frequent or infrequenct traces to explore
#' @param coverage The percentage coverage of the trace to explore.
#' @param n_traces Instead of setting coverage, you can set an exact number of traces. Should be an integer larger than 0.
#' @param min_trace_coverage The minimum coverage a trace has to be considered explore.
#' @param raw_data Return raw data
#' @param frequency Display 'relative' or 'absolute' values on plot.
#' @param .abbreviate If TRUE, abbreviate activity labels
#' @param show_labels If False, activity labels are not shown.
#' @param scale_fill Set color scale
#'
#'
#' @export trace_explorer
#'
trace_explorer <- function(eventlog,
						   coverage = NULL,
						   n_traces = NULL,
						   min_trace_coverage = NULL,
						   type = c("frequent","infrequent"),
						   .abbreviate = T,
						   show_labels = T,
						   scale_fill = scale_fill_discrete(h = c(0,360) + 15, l = 40),
						   raw_data = F,
						   frequency = c("relative", "absolute")) {

	stopifnot("eventlog" %in% class(eventlog))
	type <- match.arg(type)
	frequency <- match.arg(frequency)

	if(!is.null(coverage) && (!is.numeric(coverage) || !between(coverage,0,1) )) {
		stop("Coverage should be a numeric value between 0 and 1.")
	}
	if(!is.null(min_trace_coverage) && (!is.numeric(min_trace_coverage) || !between(min_trace_coverage,0,1) )) {
		stop("Minimum trace coverage should be a numeric value between 0 and 1.")
	}
	if(!is.null(n_traces) && n_traces <= 0)
		stop("n_traces should be greater than zero.")

	number_of_filters = 0

	if(!is.null(coverage))
	{
		number_of_filters <- number_of_filters + 1
	}

	if(!is.null(n_traces))
	{
		number_of_filters <- number_of_filters + 1
	}

	if(!is.null(min_trace_coverage))
	{
		number_of_filters <- number_of_filters + 1
	}

	if(number_of_filters == 0)
		stop("At least an coverage, n_traces or min_trace_coverage must be provided.")
	else if(number_of_filters != 1)
		stop("Cannot filter on both coverage, n_traces and min_trace_coverage simultaneously.")

	min_order <- NULL

	event_classifier <- NULL
	absolute_frequency <- NULL
	relative_frequency <- NULL
	cum_freq <- NULL
	case_classifier <- NULL
	aid <- NULL
	timestamp_classifier <- NULL
	trace_id <- NULL
	ts <- NULL
	cum_freq_lag <- NULL
	rank_event <- NULL

	eventlog %>% case_list %>%
		rename_("case_classifier" = case_id(eventlog)) -> cases

	eventlog %>% trace_list %>%
		mutate(rank_trace = row_number(-absolute_frequency)) %>%
		arrange(-relative_frequency) %>%
		mutate(cum_freq = cumsum(relative_frequency)) %>%
		mutate(cum_freq_lag = lag(cum_freq, default = 0)) -> traces

	x <- nrow(traces)

	if (!is.null(coverage))
	{
		if (type == "frequent")
		{
			traces <- traces %>% filter(cum_freq_lag < coverage)
		}
		else
		{
			traces <- traces %>% filter(cum_freq_lag > (1-coverage))
		}
	}
	else if(!is.null(n_traces))
	{
		if (type == "frequent")
		{
			traces <- traces %>% arrange(-relative_frequency) %>% slice(1:n_traces)
		}
		else
		{
			traces <- traces %>% arrange(relative_frequency) %>% slice(1:n_traces)
		}
	}
	else if(!is.null(min_trace_coverage))
	{
		if (type == "frequent")
		{
			traces <- traces %>% filter(relative_frequency >= min_trace_coverage)
		}
		else
		{
			traces <- traces %>% filter(relative_frequency < min_trace_coverage)
		}
	}

	if(is.null(coverage) && is.null(min_trace_coverage)) {
		if(x < n_traces)
		warning("Less traces found than specified number.")
	}


	if(nrow(traces) == 0) {
		stop("No traces selected. Consider increasing the coverage")
	}


	eventlog %>%
		rename_("case_classifier" = case_id(eventlog),
				"aid" = activity_instance_id(eventlog),
				"event_classifier" = activity_id(eventlog),
				"timestamp_classifier" = timestamp(eventlog)) %>%
		as.data.frame %>%
		group_by(case_classifier, event_classifier, aid) %>%
		summarize(ts = min(timestamp_classifier),
				  min_order = min(.order)) %>%
		inner_join(cases, by = "case_classifier") %>%
		group_by(trace_id) %>%
		filter(case_classifier == first(case_classifier)) %>%
		inner_join(traces, by = "trace") %>%
		arrange(ts, min_order) %>%
		mutate(rank_event = seq_len(n())) %>%
		ungroup() -> temp





	ABBR <- function(do_abbreviate) {
		if(do_abbreviate) {
			abbreviate
		} else
			function(value) {
				str_wrap(value, 20)
			}
	}


	if(raw_data)
		temp
	else {

		temp %>%
			ggplot(aes(rank_event, as.factor(trace_id))) +
			geom_tile(aes(fill = event_classifier), color = "white") +
			scale_y_discrete(breaks = NULL) +
			labs(y = "Traces", x = "Activities") +
			scale_fill  +
			labs(fill = "Activity") +
			theme_light() +
			theme(strip.text.y = element_text(angle = 0)) -> p

		if (frequency == "relative")
			p <- p + facet_grid(reorder(paste0(round(100*relative_frequency,2),"%"), -relative_frequency)~.,scales = "free", space = "free")
		else
			p <- p + facet_grid(reorder(as.character(absolute_frequency), -absolute_frequency)~.,scales = "free", space = "free")

		if(show_labels)
			p + geom_text(aes(label = ABBR(.abbreviate)(event_classifier)), color = "white",fontface = "bold")
		else
			p

	}

}

#' @rdname trace_explorer
#' @export plotly_trace_explorer

plotly_trace_explorer <- function(eventlog,
								  coverage = NULL,
								  n_traces = NULL,
								  type = c("frequent","infrequent"),
								  .abbreviate = T,
								  show_labels = T,
								  scale_fill = scale_fill_discrete(h = c(0,360) + 15, l = 40),
								  raw_data = F) {

	trace_explorer(eventlog,
				   coverage,
				   n_traces,
				   type,
				   .abbreviate,
				   show_labels,
				   scale_fill,
				   raw_data) %>%
		ggplotly
}
