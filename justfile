run-tests:
    OTEL_SDK_DISABLED=true pytest tests -vv

run-test test_name capture="no":
    OTEL_SDK_DISABLED=true pytest tests -vv --capture={{ capture }} -k {{ test_name }}
