using System;
using System.IO;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Extensions.Http;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;
using Contoso.ERP.AzureFunction;
using System.Threading;
using System.Threading.Tasks;

namespace TestFunction
{
    public class Function : AzureFunctionFunctions
    {
        public Function(IEventsDispatcher eventsDispatcher) : base(eventsDispatcher)
        {
        }

        [FunctionName("ContosoERPAzureFunction")]
        public new Task<IActionResult> Run(
            [HttpTrigger(AuthorizationLevel.Function, "post", "options", Route = null)] HttpRequest req,
            ILogger log,
            CancellationToken cancellationToken)
        {
            return base.Run(req, log, cancellationToken);
        }
    }
}
