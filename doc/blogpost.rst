Python Library for de- and encoding of WCF-Binary streams
---------------------------------------------------------

Inside of a .net environment WCF services uses the proprietary WCF-Binary-XML
protocol as described `here <https://blogs.msdn.com/b/drnick/archive/2009/09/11/binary-encoding-part-4.aspx>`_

Because of the only implementations for decoding and encoding such binary
streams exists in .net itself (and there mostly with validation and/or
auto correction features), we had decided to write our own python library
according to Microsoft's `Open Specification <http://msdn.microsoft.com/en-us/library/cc219210(v=PROT.10).aspx>`_




View and edit WCF-Binary-streams with burp 
------------------------------------------

One of fiddlers advantages are his extensibility and therefor his WCF-Binary plugins.
Sadly, this plugins could only decode and display the binary content as XML text.


The most WCF-Binary parser out there are based on the .Net library. 
Therefor you have to use Microsoft Windows, or some Mono constellation. 
Another disadvantage is the validation and auto-correction of these libraries...
not very useful for penetration testing ;-)

That's why we decided to write a small python library which enables us to decode and encode 
WCF-Binary streams. In combination with our python-to-Burp plugin we can decode, edit and 
encode WCF-Binary streams on the fly.

Due to Burps request/response life cycle you'll need three Burp instances to use 
all features. The first one decodes and encodes the data from/to the client. The 
second one operates on the XML like it was a normal request/response. The third 
one encodes/decodes the data to/from the server.
