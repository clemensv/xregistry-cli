using System;
using System.IO;
using Contoso.ERP.AzureFunction;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Contoso.ERP.AzureFunction.Contoso.ERP;


namespace TestFunction
{
    public class Function : AzureFunctionBase
    {
        public Function(IEventsDispatcher eventsDispatcher) : base(eventsDispatcher)
        {
        }

        [Function("ContosoERPAzureFunction")]
        public override Task<HttpResponseData> Run(
            [HttpTrigger(AuthorizationLevel.Function, "post", "options", Route = null)] HttpRequestData req,
            FunctionContext executionContext,
            CancellationToken cancellationToken)
        {
            return base.Run(req, executionContext, cancellationToken);
        }
    }
}
