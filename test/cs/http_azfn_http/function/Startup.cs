using Contoso.ERP.AzureFunction;
using Contoso.ERP.AzureFunction.Contoso.ERP;
using function;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

var host = new HostBuilder()
    .ConfigureFunctionsWorkerDefaults()
    .ConfigureServices(services =>
    {
        services.AddSingleton<IEventsDispatcher, MyEventsDispatcher>();
    })
    .Build();

host.Run();
