using Contoso.ERP.AzureFunction;
using Microsoft.Azure.Functions.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

[assembly: FunctionsStartup(typeof(function.Startup))]

namespace function
{
    internal class Startup : FunctionsStartup
    {
        // this is the entry point for the function
        // it registers an instance of MyEventsDispatcher as a singleton service

        private static void Main(string[] args)
        {
            var host = new HostBuilder()
                .ConfigureWebJobs(b =>
                {
                    
                })
                .ConfigureServices(s =>
                {
                    s.AddSingleton<IEventsDispatcher, MyEventsDispatcher>();
                })
                .Build();

            host.Run();
        }

        public override void Configure(IFunctionsHostBuilder builder)
        {
            builder.Services.AddSingleton<IEventsDispatcher, MyEventsDispatcher>();
        }
    }
}
