## Config file
```yaml
params:
    coil_elements:
        bad:
            - receive_coil: Head_32
              coil_elements:  HEA
            - receive_coil: Head_32
              coil_elements: HEP
        message: |
            Detected an issue with head coil elements.

            1. Check head coil connection for debris or other obstructions.
            2. Reconnect head coil securely.
            3. Ensure that anterior and posterior coil elements are present.

            Call 867-5309 for further assistance.
```
