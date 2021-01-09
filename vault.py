import smartpy as sp 


class Vault(sp.Contract):

    def __init__(self):

        self.init_type(sp.TRecord(token = sp.TNat, xtz = sp.TNat, owner = sp.TAddress,oracle = sp.TAddress, 
        Closed = sp.TBool,stablecoin = sp.TAddress,Insurance = sp.TTimestamp, securityDelegator = sp.TAddress
        ))

    @sp.entry_point
    def IncreaseCollateral(self,params):
        sp.set_type(params, sp.TRecord(amount = sp.TNat))

        sp.verify(sp.mutez(params.amount) == sp.amount)

        self.data.xtz += params.amount 
    
    @sp.entry_point
    def OpenLoan(self,params):
        sp.set_type(params, sp.TRecord(amount = sp.TNat, loan = sp.TNat))

        sp.verify(sp.sender == self.data.owner)

        sp.verify(sp.mutez(params.amount) == sp.amount)
        
        sp.verify(self.data.Closed)

        self.data.xtz += params.amount 
        self.data.token += params.loan 

        self.data.Closed = False
        c = sp.contract(sp.TRecord(loan = sp.TNat), self.data.oracle, entry_point = "MintToken").open_some()

        mydata = sp.record(loan = params.loan)

        sp.transfer(mydata, sp.mutez(0), c)

    @sp.entry_point
    def IncreaseLoan(self,params):

        sp.set_type(params, sp.TRecord(loan = sp.TNat))
        sp.verify(sp.sender == self.data.owner)

        self.data.token += params.loan 

        c = sp.contract(sp.TRecord(loan = sp.TNat), self.data.oracle, entry_point = "MintToken").open_some()

        mydata = sp.record(loan = params.loan)

        sp.transfer(mydata, sp.mutez(0), c)
    
    @sp.entry_point 
    def OracleMint(self,params):

        sp.verify(sp.sender == self.data.oracle)
        sp.set_type(params, sp.TRecord(price = sp.TNat,loan = sp.TNat))

        sp.verify(self.data.xtz * params.price*1000 >= self.data.token*150)

        # Call Validation for minting token
        c = sp.contract(sp.TRecord(value = sp.TNat , address = sp.TAddress), self.data.stablecoin, entry_point = "mint").open_some()

        mydata = sp.record(value = params.loan , address = self.data.owner)

        sp.transfer(mydata, sp.mutez(0), c)


    @sp.entry_point
    def PayBackLoan(self,params):

        sp.set_type(params, sp.TRecord(loan = sp.TNat))
        sp.verify(sp.sender == self.data.owner)
        sp.verify(self.data.token >= params.loan)

        sp.if self.data.token == params.loan: 
             
            sp.send(self.data.owner,sp.mutez(self.data.xtz))
            self.data.Closed = True
            self.data.xtz = 0 

        self.data.token = abs(self.data.token - params.loan)

        c = sp.contract(sp.TRecord(value = sp.TNat , address = sp.TAddress, owner = sp.TAddress), self.data.stablecoin, entry_point = "burn").open_some()

        mydata = sp.record(value = params.loan , address = self.data.owner, owner = self.data.owner)

        sp.transfer(mydata, sp.mutez(0), c)


    @sp.entry_point 
    def LiquidateVault(self,params):

        sp.if sp.now > self.data.Insurance:

            sp.verify(sp.amount == sp.mutez(100))
            
            c = sp.contract(sp.TRecord(address = sp.TAddress), self.data.oracle, entry_point = "LiquidateToken").open_some()

            mydata = sp.record(address = sp.sender)

            sp.transfer(mydata, sp.mutez(0), c)


    @sp.entry_point
    def OracleLiquidate(self,params):

        sp.set_type(params, sp.TRecord(address = sp.TAddress,price = sp.TNat))        

        sp.verify(sp.sender == self.data.oracle)

        sp.if self.data.xtz * params.price*1000 < self.data.token*150:

            # transfer to vault from sender 
            c = sp.contract(sp.TRecord(from_ = sp.TAddress, to_ = sp.TAddress , value = sp.TNat), self.data.stablecoin, entry_point = "transfer").open_some()
            mydata = sp.record(from_ = params.address,to_ = sp.self_address, value = self.data.token)
            sp.transfer(mydata, sp.mutez(0), c)
            
            # burn token from vault 
            d = sp.contract(sp.TRecord(value = sp.TNat , address = sp.TAddress , owner = sp.TAddress), self.data.stablecoin, entry_point = "burn").open_some()
            burndata = sp.record(value = self.data.token , address = sp.self_address, owner = self.data.owner)
            sp.transfer(burndata, sp.mutez(0), d)

            sp.send(params.address,sp.mutez(self.data.xtz))
            
            self.data.Closed = True
            self.data.xtz = 0 
            self.data.token = 0 

    @sp.entry_point
    def delegate(self, baker):
        sp.verify(sp.sender == self.data.owner)
        sp.set_delegate(baker)

    @sp.entry_point
    def UpdateCollateral(self,amount):
        sp.verify(sp.sender == self.data.owner)
        sp.verify(sp.amount == sp.mutez(0))
        sp.verify(sp.balance == sp.mutez(amount))

        self.data.xtz = amount

    @sp.entry_point
    def ReduceVault(self,params):

        sp.set_type(params, sp.TRecord(amount = sp.TNat))

        d = sp.contract(sp.TRecord(value = sp.TNat , address = sp.TAddress , owner = sp.TAddress), self.data.stablecoin, entry_point = "burn").open_some()
        
        sp.if params.amount >= self.data.token:
        
            burndata = sp.record(value = self.data.token , address = sp.self_address, owner = self.data.owner)
            self.data.Closed = True
            self.data.xtz = 0 
            self.data.token = 0 
            
            sp.send(self.data.owner,sp.mutez(self.data.xtz))

        sp.else: 
            burndata = sp.record(value = params.amount , address = sp.self_address, owner = self.data.owner)
        
        sp.transfer(burndata, sp.mutez(0), d)

    @sp.entry_point
    def TransferToken(self,params):

        sp.set_type(params, sp.TRecord(amount = sp.TNat))
        
        sp.verify(sp.sender == self.data.owner)
        sp.verify(self.data.Closed)

        c = sp.contract(sp.TRecord(from_ = sp.TAddress, to_ = sp.TAddress , value = sp.TNat), self.data.stablecoin, entry_point = "transfer").open_some()
        mydata = sp.record(from_ = sp.self_address,to_ = self.data.owner , value = params.amount)
        sp.transfer(mydata, sp.mutez(0), c)


    @sp.entry_point
    def PurchaseSecurity(self,params):
        sp.set_type(params, sp.TRecord(order = sp.TNat , duration = sp.TNat, securityDelegator = sp.TAddress))

        duration = sp.set([1,7,14])        

        sp.verify(sp.sender == self.data.owner)
        sp.verify(duration.contains(params.duration))

        self.data.Insurance =  sp.now.add_days(sp.to_int(params.duration))
        self.data.securityDelegator = params.securityDelegator
        
        c = sp.contract(sp.TRecord(xtz = sp.TNat, token = sp.TNat, order = sp.TNat , duration = sp.TNat , spender = sp.TAddress), self.data.oracle, entry_point = "SecuritiesPurchase").open_some()

        mydata = sp.record(xtz = self.data.xtz, token = self.data.token, order = params.order , duration = params.duration, spender = self.data.owner)

        sp.transfer(mydata, sp.mutez(0), c)


    @sp.entry_point
    def ExerciseSecurity(self,params):

        sp.verify(self.data.Insurance >= sp.now)

        sp.if (sp.sender == self.data.owner) | (sp.sender == self.data.securityDelegator) :
            
            self.data.Insurance = sp.now 

            c = sp.contract(sp.TRecord(owner = sp.TAddress), self.data.oracle, entry_point = "SecuritiesExercise").open_some()

            mydata = sp.record(owner = sp.self_address)

            sp.transfer(mydata, sp.mutez(0), c)


class VaultOpener(sp.Contract):

    def __init__(self,token,oracle,admin):

        self.init(
        token = token,
        oracle = oracle, 
        admin = admin,
        contract = admin
        )

        self.Vault = Vault()

    @sp.entry_point
    def OpenVault(self,params):

        self.data.contract = sp.create_contract(storage=sp.record(token=sp.nat(0),xtz=sp.nat(0),
        owner = sp.sender, oracle = self.data.oracle , Closed = True,stablecoin = self.data.token,
        Insurance = sp.now, securityDelegator = sp.sender      
        ),
        contract = self.Vault
        )

        c = sp.contract(sp.TRecord( address = sp.TAddress, owner = sp.TAddress), self.data.token, entry_point = "AddVault").open_some()

        mydata = sp.record(address = self.data.contract , owner = sp.sender)

        sp.transfer(mydata, sp.mutez(0), c)


    @sp.entry_point
    def WithdrawAdmin(self,params):

        sp.verify(sp.sender == self.data.admin)
        sp.send(self.data.admin,sp.balance)

    
if "templates" not in __name__:
    @sp.add_test(name = "FA12 StableCoin")
    def test():

        scenario = sp.test_scenario()
        scenario.h1("FA1.2 template - StableCoin")

        scenario.table_of_contents()

        # sp.test_account generates ED25519 key-pairs deterministically:
        admin = sp.test_account("Administrator")
        alice = sp.test_account("Alice")
        bob   = sp.test_account("Robert")

        # Let's display the accounts:
        scenario.h1("Accounts")
        scenario.show([admin, alice, bob])

        c1 = VaultOpener(
        sp.address("KT1HsVdNMvy4uTeorCFJD2kPVGzHXhpzJZjV"),
        sp.address("KT1LiKCNGz2NHvtUH6hhB9usqw8TfuAktusy"),
        sp.address("tz1XfbFQgxj1sSfe2YyJPba5ZQuKMcV4FXAX")
        )
        scenario += c1  

        scenario += c1.OpenVault().run(sender=alice,amount=sp.tez(1))


# vault Opener - KT1Q5SPEdRTdki5fVXS7UHikFmWA2ckd3KdA