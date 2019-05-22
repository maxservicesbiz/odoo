# Max Solutions Co + Odoo
### Community edition

## Summary 
The official website [max-solutions.co](https://max-solutions.co)

## Modules 

* ```innovt_client```
    * SaaS Controller for Max Solutions Co API
* ```innovt_invoice``` 
    * Location l10n_MX support Cfdi 3.3 
* ```innovt_payment```
    * Location l10n_MX support Payment 3.3

## Installation

* Build image 
```
    sudo docker build -t innov:11.0-ce .
```

* Using mode prodouction 
```
    sudo docker-compose -f docker-compose.yml up --build
```

* Using mode development (external db)

    * Is mandatory change the next  environment variables on `docker-compose-dev.yml`
    ```
      USER: user
      PASSWORD: password 
      HOST: host
      PORT: port
    ```
    * run 
    ```
        sudo docker-compose -f docker-compose-dev.yml up --build
    ```

## License
* [GPL 3.0](LICENSE)

## Authors 
* [Max Solutions, Co](<https://max-solutions.co>)
